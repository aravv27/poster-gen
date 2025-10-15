import os
from google import genai
import asyncio
import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from tools import Tools
from tool_config import Tool_config
from enum import Enum
from database import DatabaseManager, PhaseType, ProjectStatus
import copy
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")
client = genai.Client(api_key=api_key)
class CurrentPhase(str,Enum):
    LAYOUT = "Layout"
    CANVAS = "Canvas"
    BACKGROUND = "Background"
    ASSETS = "Assets"

class PosterRenderManager:
    def create_poster_structure(self, canvas_data):
        # Ensure canvas_data is: {"width":..., "height":..., "background":...}
        return {
            "canvas": canvas_data,  # Accept as structure or dict
            "layers": []
        }

    def add_layers_to_poster(self, poster_structure, layers_to_add, phase_type):
        # Append layers to poster's "layers" array
        if not isinstance(poster_structure.get("layers"), list):
            poster_structure["layers"] = []
        poster_structure["layers"].extend(layers_to_add)
        # No reordering, as order = render order
        return poster_structure

class Posteragent:
    def __init__(self):
        self.result_parts = []
        self.current_phase = CurrentPhase.LAYOUT
        self.db = DatabaseManager()
        self.current_project_id = None
        self.current_json = None
        self.function_call_results = []
    
    async def create_poster(self, user_prompt: str) -> str:
        """Create a complete poster through all phases autonomously"""
        try:
            # Create new project
            self.current_project_id = self.db.create_project(user_prompt)
            
            # Run all phases in sequence
            phases = [PhaseType.LAYOUT, PhaseType.CANVAS, PhaseType.BACKGROUND, PhaseType.ASSETS]
            
            for phase in phases:
                print(f"Starting {phase} phase...")
                result = await self.run_phase(user_prompt, phase)
                if "Error" in result:
                    self.db.update_project_status(self.current_project_id, ProjectStatus.PARTIAL)
                    return f"Failed at {phase} phase: {result}"
            
            # Mark project as completed
            self.db.update_project_status(self.current_project_id, ProjectStatus.COMPLETED)
            
            # Return final JSON
            final_result = self.db.get_phase_result(self.current_project_id, PhaseType.ASSETS)
            return json.dumps(final_result['json_data'], indent=2)
            
        except Exception as e:
            if self.current_project_id:
                self.db.update_project_status(self.current_project_id, ProjectStatus.FAILED)
            return f"Error creating poster: {str(e)}"

    # NEW METHOD: Run individual phase
    async def run_phase(self, user_prompt: str, phase: PhaseType) -> str:
        """Run a single phase of poster generation"""
        try:
            # Clear previous results
            self.result_parts = []
            self.function_call_results = []
            
            # Load previous phase JSON if needed
            previous_json = self.db.get_current_json_for_next_phase(self.current_project_id, phase)
            self.current_json = previous_json
            
            # Build context for this phase
            context = await self.build_context(user_prompt, phase.value)
            
            # Build tools for this phase
            tool_list = await self.build_tools(phase)
            
            print(f"\nContext for {phase}:")
            #print(context)
            print(f"\nTools for {phase}:")
            #print(json.dumps(tool_list, indent=2))

            # Generate response
            print(f"\nGenerating response for {phase}...")
            #print("\nSending to Gemini with tools:", json.dumps(tool_list, indent=2))
            # Configure generation parameters
            
            response = await asyncio.to_thread(
                client.models.generate_content,
                model='gemini-2.5-flash',  # Use the correct model name
                contents=context,
                config={'tools': [{'function_declarations': tool_list}]}  # Pass tools in the correct format
            )
            
            print("\nAPI Response:")
            print(response.candidates[0].content)

            if response.candidates[0].content.parts is None:
                print(f"\n⚠️ No function calls generated for {phase} phase")
                print("This phase will be skipped (no assets needed)")
            
            # Use previous JSON as-is since no changes needed
                if self.current_json:
                    self.db.save_phase_result(self.current_project_id, phase, self.current_json)
                return "Phase completed (no changes needed)"
            
            # Process response
            print("\nProcessing response parts...")
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text is not None:
                    #print(f"Found text: {part.text}")
                    self.result_parts.append(part.text)
                if hasattr(part, "function_call") and part.function_call is not None:
                    #print(f"Found function call: {part.function_call.name}")
                    #print(f"With arguments: {part.function_call.args}")
                    self.process_function_call(part.function_call)
            
            # Update JSON and save to database
            updated_json = await self.update_json_with_results(phase)
            print("Saving phase result, phase:", phase)
            print("Project ID:", self.current_project_id, type(self.current_project_id))
            print("Phase:", phase, type(phase))
            print("Updated JSON:", type(updated_json))

            self.db.save_phase_result(self.current_project_id, phase, updated_json)
            
            # Debug: Print current phase result
            print(f"\n=== {phase} Phase Result ===")
            print(json.dumps(updated_json, indent=2))
            print("====================\n")
            
            # Update project current phase
            next_phases = {
                PhaseType.LAYOUT: PhaseType.CANVAS,
                PhaseType.CANVAS: PhaseType.BACKGROUND, 
                PhaseType.BACKGROUND: PhaseType.ASSETS,
                PhaseType.ASSETS: None
            }
            
            next_phase = next_phases.get(phase)
            if next_phase:
                self.db.update_project_status(self.current_project_id, ProjectStatus.ACTIVE, next_phase)
            
            return "Phase completed successfully"
            
        except Exception as e:
            return f"Error in {phase} phase: {str(e)}"

    async def update_json_with_results(self, phase: PhaseType) -> dict:
        """Updated method that creates your exact render.py JSON schema"""
        
        if phase == PhaseType.LAYOUT:
            if self.function_call_results:
                return self.function_call_results[0]
            return {}
        
        elif phase == PhaseType.CANVAS:
            # Canvas phase creates the base structure
            if not self.current_json or not self.function_call_results:
                return self.current_json or {}
            
            updated_json = copy.deepcopy(self.current_json)
            canvas_results = self.function_call_results
            canvas_index = 0
            
            def replace_canvas_placeholders(obj):
                nonlocal canvas_index
                if isinstance(obj, dict):
                    for key, value in list(obj.items()):  # Use list to safely mutate
                        if key.startswith("canvas_") and value == "PLACEHOLDER":
                            if canvas_index < len(canvas_results):
                                canvas_data = canvas_results[canvas_index]
                                # FIX: Unwrap if needed
                                if isinstance(canvas_data, dict) and "canvas" in canvas_data:
                                    canvas_data = canvas_data["canvas"]
                                poster_manager = PosterRenderManager()
                                obj[key] = poster_manager.create_poster_structure(canvas_data)
                                canvas_index += 1
                        elif isinstance(value, (dict, list)):
                            replace_canvas_placeholders(value)
                elif isinstance(obj, list):
                    for item in obj:
                        replace_canvas_placeholders(item)

            
            replace_canvas_placeholders(updated_json)
            return updated_json
        
        elif phase in [PhaseType.BACKGROUND, PhaseType.ASSETS]:
            # Add layers to existing poster structures
            if not self.current_json or not self.function_call_results:
                return self.current_json or {}
            
            updated_json = copy.deepcopy(self.current_json)
            layer_results = self.function_call_results
            layer_index = 0
            
            def add_layers_to_posters(obj):
                nonlocal layer_index
                
                if isinstance(obj, dict):
                    # Check if this is a poster structure (has canvas and layers)
                    if "canvas" in obj and "layers" in obj:
                        if layer_index < len(layer_results):
                            poster_manager = PosterRenderManager()
                            layer_data = layer_results[layer_index]
                            
                            # Handle both single layers and arrays
                            layers_to_add = layer_data if isinstance(layer_data, list) else [layer_data]
                            
                            obj = poster_manager.add_layers_to_poster(obj, layers_to_add, phase)
                            layer_index += 1
                    
                    # Recurse into nested structures
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            obj[key] = add_layers_to_posters(value)
                
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        obj[i] = add_layers_to_posters(item)
                
                return obj
            
            return add_layers_to_posters(updated_json)
        
        return self.current_json or {}


    # UPDATED METHOD: Enhanced process_function_call to store results
    def process_function_call(self, function_call):
        args = function_call.args
        fn = function_call.name
        
        result = None
        
        if fn == "generate_canvas":
            result = Tools.generate_canvas(
                width=int(args.get("width", 800)),
                height=int(args.get("height", 600)), 
                background=args.get("background", "#000000")
            )
        elif fn == "generate_layout":
            result = Tools.generate_layout(
                layout_string=args.get("layout_string")
            )
        elif fn == "generate_radial_gradient":
            result = Tools.generate_radial_gradient(
                colors=args.get("colors"),
                stops=args.get("stops"),
                start_color=args.get("start_color"),
                end_color=args.get("end_color"),
                x=args.get("x", "50%"),
                y=args.get("y", "50%"),
                width=args.get("width"),
                height=args.get("height"),
                opacity=args.get("opacity", 1.0),
                anchor=args.get("anchor", "top-left")
            )
        elif fn == "generate_linear_gradient":
            result = Tools.generate_linear_gradient(
                colors=args.get("colors"),
                stops=args.get("stops"),
                angle=args.get("angle", 0),
                opacity=args.get("opacity", 1.0),
                width=args.get("width"),
                height=args.get("height"),
                anchor=args.get("anchor", "top-left")
            )
        elif fn == "generate_mesh_gradient":
            result = Tools.generate_mesh_gradient(
                mesh_points=args.get("mesh_points"),
                opacity=args.get("opacity", 1.0)
            )
        elif fn == "generate_shape_blur_gradient":
            result = Tools.generate_shape_blur_gradient(
                colors=args.get("colors"),
                stops=args.get("stops"),
                angle=args.get("angle"),
                shape_gradient_type=args.get("shape_gradient_type", "linear"),
                shape=args.get("shape", "ellipse"),
                shape_x=args.get("shape_x", "0%"),
                shape_y=args.get("shape_y", "0%"),
                shape_width=args.get("shape_width", "100%"),
                shape_height=args.get("shape_height", "100%"),
                blur_radius=args.get("blur_radius", 20),
                opacity=args.get("opacity", 1.0)
            )
        elif fn == "generate_color_overlay":
            result = Tools.generate_color_overlay(
                color=args.get("color"),
                width=args.get("width"),
                height=args.get("height"),
                x=args.get("x", 0),
                y=args.get("y", 0),
                anchor=args.get("anchor", "top-left"),
                opacity=args.get("opacity", 1.0),
                blur=args.get("blur", 0)
            )
        # NEW ASSET LAYER FUNCTIONS
        elif fn == "generate_image_layer":
            result = Tools.generate_image_layer(
                src=args.get("src"),
                x=args.get("x", 0),
                y=args.get("y", 0),
                anchor=args.get("anchor", "top-left"),
                width=args.get("width"),
                height=args.get("height"),
                opacity=args.get("opacity", 1.0),
                angle=args.get("angle", 0),
                flip=args.get("flip", False),
                flop=args.get("flop", False),
                filters=args.get("filters")
            )
        elif fn == "generate_text_layer":
            result = Tools.generate_text_layer(
                text=args.get("text"),
                x=args.get("x", 0),
                y=args.get("y", 0),
                anchor=args.get("anchor", "top-left"),
                font=args.get("font"),
                size=int(args.get("size", 32)),
                color=args.get("color", "#ffffff"),
                align=args.get("align", "left"),
                opacity=args.get("opacity", 1.0),
                weight=args.get("weight", "normal"),
                stroke_color=args.get("stroke_color"),
                stroke_width=int(args.get("stroke_width", 0)),
                line_height=float(args.get("line_height", 1.0)),
                letter_spacing=int(args.get("letter_spacing", 0)),
                transform=args.get("transform"),
                shadow=args.get("shadow")
            )
        elif fn == "generate_ellipse":
            result = Tools.generate_ellipse(
                color=args.get("color"),
                x=args.get("x", 0),
                y=args.get("y", 0),
                width=args.get("width", 100),
                height=args.get("height", 100),
                anchor=args.get("anchor", "top-left"),
                opacity=args.get("opacity", 1.0),
                blur=int(args.get("blur", 0))
            )
        elif fn == "generate_polygon":
            result = Tools.generate_polygon(
                color=args.get("color"),
                points=args.get("points"),
                opacity=args.get("opacity", 1.0),
                blur=int(args.get("blur", 0))
            )
        
        # Store result for positional mapping
        if result:
            self.function_call_results.append(result)
            self.result_parts.append(json.dumps(result, indent=2))

    # NEW METHOD: Build context for each phase
    async def build_context(self, input: str, phase: str) -> str:
        print(f"Building context for phase {phase} with input: {input}")  # Debug print

        # Convert PhaseType enum to string if needed
        if isinstance(phase, PhaseType):
            phase = phase.value

        if phase.lower() == "layout":
            return (
                "You are an autonomous layout agent for an enterprise poster design system.\n"
                "TASK:\n"
                "  - Output a single valid generate_layout TOOL CALL, nothing else.\n"
                "  - NEVER write explanations, chat, or markdown.\n"
                "All placeholders MUST only specify size (percent or pixel). No CSS, background, style, or visual data can appear in the layout string. For example: placeholder(10%), not placeholder(…, background: …) or similar. All background/design must be expressed later as layers"
                "POSTER REQUEST:\n"
                f"{input}\n"
                "REQUIREMENTS:\n"
                "  - Use 'container(widthxheight)[content]' syntax ONLY.\n"
                "  - Use only the following structure keywords: container, row, column, stack, placeholder.\n"
                "  - Each call must cover the FULL layout as a single tree.\n"
                "EXAMPLES:\n"
                "  - container(800x600)[column[placeholder(20%), placeholder(60%), placeholder(20%)]]\n"
                "  - container(800x600)[row[placeholder(50%), placeholder(50%)]]\n"
                "  - container(1200x800)[column[placeholder(20%), row[placeholder(40%), placeholder(40%)]]]\n"
                "ONLY output a single generate_layout(...), no extra text."
            )

        elif phase.lower() == "canvas":
            canvas_count = self.count_placeholders(self.current_json)
            return (
                "You are an autonomous canvas configuration agent for enterprise poster design.\n"
                f"- There are {canvas_count} canvases to define based strictly on the current layout.\n"
                "- For EACH placeholder, output one generate_canvas TOOL CALL only—never chat or explain.\n"
                "- Always specify width, height, and background. Use JSON input for correct dimensions.\n"
                f"- LAYOUT CONTEXT (read-only):\n{json.dumps(self.current_json, indent=2)}\n"
                "Output NOTHING but valid generate_canvas calls in response."
                "POSTER REQUEST:\n"
                f"{input}\n"
            )

        elif phase.lower() == "background":
            canvas_info = self.analyze_canvas_structure(self.current_json)
            return (
                "You are the autonomous background phase agent for poster design.\n"
                "- Output strictly JSON-compatible TOOL CALLS for background generation (one per canvas).\n"
                "- Allowed tools: generate_radial_gradient, generate_linear_gradient, generate_mesh_gradient, generate_shape_blur_gradient, generate_color_overlay.\n"
                f"- CANVAS METADATA (read-only):\n{json.dumps(canvas_info, indent=2)}\n"
                "- Do NOT output ANY natural language, markdown, or explanations.\n"
                "Output valid background tool calls. Only that."
                "POSTER REQUEST:\n"
                f"{input}\n"
            )

        elif phase.lower() == "assets":
            canvas_info = self.analyze_canvas_structure(self.current_json)
            return (
                "You are the final rendering agent for poster design content layers (assets).\n"
                "- For each canvas, output ONLY valid JSON tool calls for the content asset tools:\n"
                "  - generate_text_layer, generate_image_layer, generate_ellipse, generate_polygon\n"
                "- Each tool call describes ONE content layer; output in draw order (back to front).\n"
                "- Do not chat, explain, or use markdown. Only emit valid tool calls—no text.\n"
                f"- CANVAS CONTEXT:\n{json.dumps(canvas_info, indent=2)}\n"
                "Place each tool call directly in your output, nothing else."
                "POSTER REQUEST:\n"
                f"{input}\n"
            )

        return ""

    # NEW HELPER METHOD: Count placeholders in layout
    def count_placeholders(self, json_obj):
        """Count the number of canvas placeholders in the JSON"""
        if not json_obj:
            return 0
        
        count = 0
        def count_recursive(obj):
            nonlocal count
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith("canvas_") and value == "PLACEHOLDER":
                        count += 1
                    elif isinstance(value, (dict, list)):
                        count_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    count_recursive(item)
        
        count_recursive(json_obj)
        return count

    # NEW HELPER METHOD: Analyze canvas structure
    def analyze_canvas_structure(self, json_obj):
        """Analyze canvas structure for context building"""
        if not json_obj:
            return "No canvas structure available"
        
        canvases = []
        canvas_index = 0
        
        def find_canvases(obj):
            nonlocal canvas_index
            if isinstance(obj, dict):
                if "canvas" in obj and isinstance(obj["canvas"], dict):
                    canvas_info = {
                        "index": canvas_index,
                        "width": obj["canvas"].get("width", "unknown"),
                        "height": obj["canvas"].get("height", "unknown"),
                        "background": obj["canvas"].get("background", "unknown"),
                        "has_layers": "layers" in obj and len(obj.get("layers", [])) > 0
                    }
                    canvases.append(canvas_info)
                    canvas_index += 1
                
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        find_canvases(value)
            elif isinstance(obj, list):
                for item in obj:
                    find_canvases(item)
        
        find_canvases(json_obj)
        return canvases
    
    async def build_tools(self, phase: str) -> list:
        print(f"\nBuilding tools for phase: {phase}")
        
        # Convert PhaseType enum to string if needed
        if isinstance(phase, PhaseType):
            phase = phase.value
        phase = phase.lower()
        
        # Clean tool configurations - remove 'examples' and other invalid fields
        def clean_tool_config(tool_config):
            """Clean tool config by removing invalid fields like 'examples'"""
            cleaned = {
                "name": tool_config["name"],
                "description": tool_config["description"],
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": tool_config["parameters"].get("required", [])
                }
            }
            
            # Clean properties - remove 'examples' field
            for prop_name, prop_config in tool_config["parameters"]["properties"].items():
                cleaned_prop = {}
                for key, value in prop_config.items():
                    if key != "examples":  # Skip the 'examples' field that's causing the error
                        cleaned_prop[key] = value
                cleaned["parameters"]["properties"][prop_name] = cleaned_prop
                
            return cleaned
        
        # Define tool configurations
        if phase == "canvas":
            tools = [clean_tool_config(Tool_config.canvas_tool)]
        elif phase == "background":
            tools = [
                clean_tool_config(Tool_config.color_overlay_tool),
                clean_tool_config(Tool_config.linear_gradient_tool),
                clean_tool_config(Tool_config.mesh_gradient_tool),
                clean_tool_config(Tool_config.radial_gradient_tool),
                clean_tool_config(Tool_config.shape_blur_gradient_tool)
            ]
        elif phase == "layout":
            tools = [clean_tool_config(Tool_config.generate_layout)]
        elif phase == "assets":
            tools = [
                clean_tool_config(Tool_config.generate_ellipse),
                clean_tool_config(Tool_config.generate_image_layer),
                clean_tool_config(Tool_config.generate_polygon),
                clean_tool_config(Tool_config.generate_text_layer)
            ]
        else:
            print(f"Warning: No tools found for phase {phase}")
            return []
        """
        print(f"Providing {len(tools)} tools for {phase} phase:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
        """
            
        return tools


async def main():
    agent = Posteragent()
    user_prompt = """Design a poster background using only gradients—no images.
    USE TEXT to tell some ideas. Dont miss the text.
Create a layered, modern, and clean tech aesthetic reminiscent of AI, math, or digital transformation.

Instructions:
- Use multiple gradients (radial, linear, and mesh).
- Emphasize blue, violet, cyan, and subtle dark shades for depth.
- Create soft, glowing, blended transitions—no hard edges.
- Add at least one or two overlapping gradients to form bright areas and subtle, digital-looking blends.
- Use at least one mesh or multi-point radial gradient for a “datamap” or “AI” effect, with blended nodes or light regions.
- Use dark blue/black as the base to keep the poster modern and tech-savvy.
- No logos, or icons—color, transitions, and soft blurs only.
- FILL ALL THE CANVAS NEEDED PROPERLY, DONT LEAVE ANY PLACEHOLDERS EMPTY

Goal:
- The effect should be futuristic, abstract, and hint at organized complexity (order-from-chaos), similar to cosmic or neural network visuals.
- The background should be visually interesting, ready for a logo or text to be placed later, but should not itself contain any focal objects.

Palette: #19202e, #232946, #3066be, #b0b9e7, #bbdfff, #aac7e7, #9a89d9, #e3eefa, #6fd1fb, #8c6be5
"""
    print("\nStarting poster generation with prompt:", user_prompt)
    print("\nThis will go through multiple phases (Layout → Canvas → Background → Assets)")
    result = await agent.create_poster(user_prompt)
    print("\nFinal Poster JSON:")
    print(result)

asyncio.run(main())
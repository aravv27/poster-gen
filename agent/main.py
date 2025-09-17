import os
from google import genai
import asyncio
import json
import sqlite3
from typing import Dict, List, Optional
from pydantic import BaseModel
from tools import Tools
from tool_config import Tool_config
from enum import Enum
from dotenv import load_dotenv
load_dotenv()
client  = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
class CurrentPhase(str,Enum):
    CANVAS = "Canvas"
    BACKGROUND = "Background"
    IMAGES_SHAPES = "Images_shapes"
    TEXT = "Text"


class Posteragent:
    def __init__(self):
        self.result_parts = []
        self.current_phase = CurrentPhase.CANVAS

    async def generate_response(self,input: str,phase:str = 'Canvas') -> str:
        try:
            context = await self.build_context(input,phase)

            tool_list = await self.build_tools(phase)

            response = await asyncio.to_thread(
                client.models.generate_content,
                model = 'gemini-2.5-flash',
                contents =  context,
                config={'tools': [{'function_declarations': [tool_list]}]}
            )

            #print("Full response candidates:", response.candidates)
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text is not None:
                    self.result_parts.append(part.text)
                if hasattr(part,"function_call") and part.function_call is not None:
                    function_call = part.function_call
                    if function_call.name == "generate_canvas":
                        self.process_function_call(function_call)
                    
            return "\n".join(self.result_parts) if self.result_parts else "No response generated"
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    async def build_context(self,input: str,phase:str) -> str:
        context = ""
        if phase == "Canvas":
            return 
        elif phase == "Background":
            return
    async def build_tools(self,phase:str) -> list:
        if phase == "Canvas":
            return [Tool_config.canvas_tool]
        elif phase == "Background":
            return [Tool_config.color_overlay_tool,Tool_config.linear_gradient_tool,Tool_config.mesh_gradient_tool,Tool_config.radial_gradient_tool,Tool_config.shape_blur_gradient_tool]

    def process_function_call(self,function_call):
        args = function_call.args
        fn = function_call.name

        if fn == "generate_canvas":
            canvas_result = Tools.generate_canvas(
                width=int(args.get("width", 800)),
                height=int(args.get("height", 600)), 
                background=args.get("background", "#000000")
            )
            self.result_parts.append(json.dumps(canvas_result, indent=2))

        elif fn == "generate_radial_gradient":
            radial_result = Tools.generate_radial_gradient(
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
            self.result_parts.append(json.dumps(radial_result, indent=2))

        elif fn == "generate_linear_gradient":
            linear_result = Tools.generate_linear_gradient(
                colors=args.get("colors"),
                stops=args.get("stops"),
                angle=args.get("angle", 0),
                opacity=args.get("opacity", 1.0),
                width=args.get("width"),
                height=args.get("height"),
                anchor=args.get("anchor", "top-left")
            )
            self.result_parts.append(json.dumps(linear_result, indent=2))

        elif fn == "generate_mesh_gradient":
            mesh_result = Tools.generate_mesh_gradient(
                mesh_points=args.get("mesh_points"),
                opacity=args.get("opacity", 1.0)
            )
            self.result_parts.append(json.dumps(mesh_result, indent=2))

        elif fn == "generate_shape_blur_gradient":
            shape_blur_result = Tools.generate_shape_blur_gradient(
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
            self.result_parts.append(json.dumps(shape_blur_result, indent=2))

        elif fn == "generate_color_overlay":
            color_overlay_result = Tools.generate_color_overlay(
                color=args.get("color"),
                width=args.get("width"),
                height=args.get("height"),
                x=args.get("x", 0),
                y=args.get("y", 0),
                anchor=args.get("anchor", "top-left"),
                opacity=args.get("opacity", 1.0),
                blur=args.get("blur", 0)
            )
            self.result_parts.append(json.dumps(color_overlay_result, indent=2))

        
agent = Posteragent()
result = asyncio.run(agent.generate_response("Create a canvas that is apporiate for a a4 with DPI 300 sheet with a cream background",'Canvas'))
print(result)

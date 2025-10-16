# def translate_canvas_numbering(llm_output: dict) -> dict:
#     """
#     Translate LLM output with canvas_N numbering to render engine format.
    
#     Features:
#     1. Unwraps canvas_N keys and flattens structure
#     2. Auto-converts stack → column when detecting vertical layout pattern
#     3. Adds appropriate width/height constraints based on layout type
#     4. Sanitizes dimension values (removes 'px' suffix)
#     5. Enforces semantic constraints for layout types
#     """
    
#     def sanitize_dimension(value):
#         """
#         Convert dimension values to render engine format.
#         '1920px' → 1920
#         '50%' → '50%'
#         1920 → 1920
#         """
#         if isinstance(value, str):
#             # Remove 'px' suffix
#             if value.endswith('px'):
#                 try:
#                     return int(value[:-2])
#                 except ValueError:
#                     return value
#             # Keep percentages as-is
#             elif value.endswith('%'):
#                 return value
#             # Try to convert plain string numbers
#             else:
#                 try:
#                     return int(value)
#                 except ValueError:
#                     return value
#         return value
    
#     def sanitize_layer(layer):
#         """Sanitize all dimension fields in a layer"""
#         if not isinstance(layer, dict):
#             return layer
        
#         # Fields that might have 'px' suffix
#         dimension_fields = ['width', 'height', 'x', 'y', 'shape_width', 'shape_height', 
#                            'shape_x', 'shape_y', 'blur_radius', 'blur']
        
#         sanitized = {}
#         for key, value in layer.items():
#             if key in dimension_fields:
#                 sanitized[key] = sanitize_dimension(value)
#             elif isinstance(value, dict):
#                 sanitized[key] = sanitize_layer(value)
#             elif isinstance(value, list):
#                 sanitized[key] = [sanitize_layer(item) if isinstance(item, dict) else item for item in value]
#             else:
#                 sanitized[key] = value
        
#         return sanitized
    
#     def should_convert_stack_to_column(stack_data):
#         """
#         Detect if a stack should actually be a column.
#         If all children have explicit canvas heights, it's likely a vertical layout.
#         """
#         if "children" not in stack_data:
#             return False
            
#         children = stack_data["children"]
#         if len(children) <= 1:
#             return False
        
#         # Check if multiple children have canvases with explicit heights
#         canvas_count = 0
#         for child in children:
#             if isinstance(child, dict):
#                 # Look for canvas_N pattern with height
#                 for key, value in child.items():
#                     if key.startswith("canvas_") and isinstance(value, dict):
#                         if "canvas" in value and "height" in value["canvas"]:
#                             canvas_count += 1
#                             break
        
#         # If 2+ children have explicit canvas heights, likely a column layout
#         return canvas_count >= 2
    
#     def enforce_stack_semantics(children):
#         """
#         Enforce stack semantics: all children must be 100% x 100% to overlay properly.
#         Stack children layer on top of each other, so they should fill the container.
#         """
#         for child in children:
#             if isinstance(child, dict):
#                 child["width"] = "100%"
#                 child["height"] = "100%"
#                 print(f"  ✓ Stack child: enforced width=100%, height=100%")
    
#     def enforce_column_semantics(children):
#         """
#         Enforce column semantics: heights should be properly distributed.
#         Only fix if all children use percentages and they don't sum to ~100%.
#         """
#         if not children:
#             return
        
#         # Check if all children have percentage heights
#         percentage_heights = []
#         has_non_percentage = False
        
#         for child in children:
#             if isinstance(child, dict):
#                 height = child.get("height")
#                 if height is None:
#                     percentage_heights.append(None)
#                 elif isinstance(height, str) and height.endswith('%'):
#                     try:
#                         percentage_heights.append(float(height[:-1]))
#                     except ValueError:
#                         has_non_percentage = True
#                         break
#                 else:
#                     # Pixel value or other format
#                     has_non_percentage = True
#                     break
        
#         # If any non-percentage values or missing heights, redistribute
#         if has_non_percentage or None in percentage_heights:
#             # Distribute evenly
#             height_percent = round(100 / len(children), 2)
#             for child in children:
#                 if isinstance(child, dict):
#                     child["height"] = f"{height_percent}%"
#             print(f"  ⚠️  Column: redistributed heights evenly ({height_percent}% each)")
#         else:
#             # All percentages - check if they sum to ~100%
#             total = sum(percentage_heights)
#             if total < 95 or total > 105:
#                 # Doesn't sum to 100%, redistribute
#                 height_percent = round(100 / len(children), 2)
#                 for child in children:
#                     if isinstance(child, dict):
#                         child["height"] = f"{height_percent}%"
#                 print(f"  ⚠️  Column: heights sum to {total}%, redistributed to {height_percent}% each")
#             else:
#                 print(f"  ✓ Column: heights properly distributed (sum={total}%)")
    
#     def enforce_row_semantics(children):
#         """
#         Enforce row semantics: widths should be properly distributed.
#         Only fix if all children use percentages and they don't sum to ~100%.
#         """
#         if not children:
#             return
        
#         # Check if all children have percentage widths
#         percentage_widths = []
#         has_non_percentage = False
        
#         for child in children:
#             if isinstance(child, dict):
#                 width = child.get("width")
#                 if width is None:
#                     percentage_widths.append(None)
#                 elif isinstance(width, str) and width.endswith('%'):
#                     try:
#                         percentage_widths.append(float(width[:-1]))
#                     except ValueError:
#                         has_non_percentage = True
#                         break
#                 else:
#                     # Pixel value or other format
#                     has_non_percentage = True
#                     break
        
#         # If any non-percentage values or missing widths, redistribute
#         if has_non_percentage or None in percentage_widths:
#             # Distribute evenly
#             width_percent = round(100 / len(children), 2)
#             for child in children:
#                 if isinstance(child, dict):
#                     child["width"] = f"{width_percent}%"
#             print(f"  ⚠️  Row: redistributed widths evenly ({width_percent}% each)")
#         else:
#             # All percentages - check if they sum to ~100%
#             total = sum(percentage_widths)
#             if total < 95 or total > 105:
#                 # Doesn't sum to 100%, redistribute
#                 width_percent = round(100 / len(children), 2)
#                 for child in children:
#                     if isinstance(child, dict):
#                         child["width"] = f"{width_percent}%"
#                 print(f"  ⚠️  Row: widths sum to {total}%, redistributed to {width_percent}% each")
#             else:
#                 print(f"  ✓ Row: widths properly distributed (sum={total}%)")
    
#     def process_node(node, parent_context=None):
#         """Recursively process each node in the JSON tree"""
        
#         if not isinstance(node, dict):
#             return node
        
#         processed = {}
        
#         for key, value in node.items():
#             # Check if this is a canvas_N key
#             if key.startswith("canvas_") and isinstance(value, dict):
#                 if "canvas" in value and "layers" in value:
#                     # Flatten the structure and sanitize layers
#                     processed["canvas"] = value["canvas"]
#                     processed["layers"] = [sanitize_layer(layer) for layer in value.get("layers", [])]
#                 else:
#                     processed[key] = process_node(value, parent_context)
            
#             # Handle stack with fallback conversion
#             elif key == "stack" and isinstance(value, dict):
#                 # Check if this should be a column instead
#                 if should_convert_stack_to_column(value):
#                     print("⚠️  Auto-converting 'stack' → 'column' (detected vertical layout pattern)")
#                     layout_context = {"type": "column"}
#                     processed["column"] = process_node(value, layout_context)
#                 else:
#                     layout_context = {"type": "stack"}
#                     processed[key] = process_node(value, layout_context)
            
#             # Handle other layout containers
#             elif key in ["column", "row"] and isinstance(value, dict):
#                 layout_context = {"type": key}
#                 processed[key] = process_node(value, layout_context)
            
#             # Handle children arrays
#             elif key == "children" and isinstance(value, list):
#                 processed[key] = []
#                 num_children = len(value)
                
#                 for child in value:
#                     processed_child = process_node(child, parent_context)
#                     processed[key].append(processed_child)
                
#                 # Enforce semantic constraints AFTER processing all children
#                 if parent_context:
#                     layout_type = parent_context.get("type")
                    
#                     if layout_type == "stack":
#                         print(f"Enforcing stack semantics for {num_children} children:")
#                         enforce_stack_semantics(processed[key])
                    
#                     elif layout_type == "column":
#                         print(f"Enforcing column semantics for {num_children} children:")
#                         enforce_column_semantics(processed[key])
                    
#                     elif layout_type == "row":
#                         print(f"Enforcing row semantics for {num_children} children:")
#                         enforce_row_semantics(processed[key])
            
#             # Sanitize layers array
#             elif key == "layers" and isinstance(value, list):
#                 processed[key] = [sanitize_layer(layer) for layer in value]
            
#             # Handle container
#             elif key == "container" and isinstance(value, dict):
#                 processed[key] = process_node(value, parent_context)
            
#             # Keep all other keys as-is
#             else:
#                 if isinstance(value, dict):
#                     processed[key] = process_node(value, parent_context)
#                 elif isinstance(value, list):
#                     processed[key] = [process_node(item, parent_context) if isinstance(item, dict) else item for item in value]
#                 else:
#                     processed[key] = value
        
#         return processed
    
#     return process_node(llm_output)

import random
import json

def translate_canvas_numbering(llm_output: dict, phase: str = "assets") -> dict:
    """
    Translate LLM output with canvas_N numbering to render engine format.
    
    Args:
        llm_output: The JSON output from the LLM agent
        phase: Current phase - "layout", "canvas", "background", or "assets"
    
    Features:
    1. Phase-aware translation with render-ready output for each phase
    2. Unwraps canvas_N keys and flattens structure
    3. Adds placeholder canvases for layout-only phase (visualization only)
    4. Enforces semantic constraints for stack/column/row
    5. Sanitizes dimension values (removes 'px' suffix)
    """
    
    # Generate random colors for layout visualization
    def get_random_color():
        """Generate a random hex color for layout visualization"""
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788"
        ]
        return random.choice(colors)
    
    def sanitize_dimension(value):
        """
        Convert dimension values to render engine format.
        '1920px' → 1920
        '50%' → '50%'
        1920 → 1920
        """
        if isinstance(value, str):
            # Remove 'px' suffix
            if value.endswith('px'):
                try:
                    return int(value[:-2])
                except ValueError:
                    return value
            # Keep percentages as-is
            elif value.endswith('%'):
                return value
            # Try to convert plain string numbers
            else:
                try:
                    return int(value)
                except ValueError:
                    return value
        return value
    
    def sanitize_layer(layer):
        """Sanitize all dimension fields in a layer"""
        if not isinstance(layer, dict):
            return layer
        
        # Fields that might have 'px' suffix
        dimension_fields = ['width', 'height', 'x', 'y', 'shape_width', 'shape_height', 
                           'shape_x', 'shape_y', 'blur_radius', 'blur']
        
        sanitized = {}
        for key, value in layer.items():
            if key in dimension_fields:
                sanitized[key] = sanitize_dimension(value)
            elif isinstance(value, dict):
                sanitized[key] = sanitize_layer(value)
            elif isinstance(value, list):
                sanitized[key] = [sanitize_layer(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def create_placeholder_canvas(width=800, height=600, color=None):
        """Create a placeholder canvas for layout visualization"""
        if color is None:
            color = get_random_color()
        
        return {
            "canvas": {
                "width": width,
                "height": height,
                "background": "#FFFFFF"
            },
            "layers": [
                {
                    "type": "color_overlay",
                    "color": color,
                    "opacity": 0.3  # Semi-transparent so you can see structure
                }
            ]
        }
    
    def inject_placeholder_canvases(node, parent_context=None):
        """
        For layout phase: Inject placeholder canvases into leaf nodes.
        This makes the structure renderable for visualization.
        """
        if not isinstance(node, dict):
            return node
        
        result = {}
        
        # Check if this is a layout container
        is_container = any(key in node for key in ['container', 'column', 'row', 'stack'])
        
        if is_container:
            # Process container nodes recursively
            for key, value in node.items():
                if key in ['container', 'column', 'row', 'stack']:
                    result[key] = inject_placeholder_canvases(value, {"type": key})
                else:
                    result[key] = inject_placeholder_canvases(value, parent_context)
        
        elif 'children' in node:
            # Process children array
            result['children'] = []
            for child in node['children']:
                processed_child = inject_placeholder_canvases(child, parent_context)
                result['children'].append(processed_child)
            
            # Copy other keys
            for key, value in node.items():
                if key != 'children':
                    result[key] = value
        
        else:
            # Leaf node - check if it needs a placeholder canvas
            has_canvas = any(k.startswith('canvas_') or k == 'canvas' for k in node.keys())
            
            if not has_canvas:
                # Add placeholder canvas for visualization
                placeholder = create_placeholder_canvas()
                result.update(placeholder)
                print(f"  → Added placeholder canvas for layout visualization")
            
            # Copy all original keys
            for key, value in node.items():
                result[key] = inject_placeholder_canvases(value, parent_context) if isinstance(value, dict) else value
        
        return result
    
    def ensure_canvas_structure(node):
        """
        For canvas/background/assets phases: Ensure all canvas_N have proper structure.
        """
        if not isinstance(node, dict):
            return node
        
        result = {}
        
        for key, value in node.items():
            if key.startswith('canvas_'):
                # Ensure canvas_N has both 'canvas' and 'layers'
                if isinstance(value, dict) and 'canvas' in value:
                    result[key] = {
                        'canvas': value['canvas'],
                        'layers': value.get('layers', [])
                    }
                elif value == "PLACEHOLDER":
                    result[key] = {
                    "canvas": {
                        "width": 800,  # Use proper width/height as needed
                        "height": 600,
                        "background": "#FFFFFF"
                    },
                    "layers": []
                }
                else:
                    # Malformed canvas_N - try to fix
                    print(f"  ⚠️ Malformed {key}, attempting to fix...")
                    result[key] = value
            else:
                # Recursively process other nodes
                if isinstance(value, dict):
                    result[key] = ensure_canvas_structure(value)
                elif isinstance(value, list):
                    result[key] = [ensure_canvas_structure(item) if isinstance(item, dict) else item for item in value]
                else:
                    result[key] = value
        
        return result
    
    def should_convert_stack_to_column(stack_data):
        """
        Detect if a stack should actually be a column.
        If all children have explicit canvas heights, it's likely a vertical layout.
        """
        if "children" not in stack_data:
            return False
            
        children = stack_data["children"]
        if len(children) <= 1:
            return False
        
        # Check if multiple children have canvases with explicit heights
        canvas_count = 0
        for child in children:
            if isinstance(child, dict):
                # Look for canvas_N pattern with height
                for key, value in child.items():
                    if key.startswith("canvas_") and isinstance(value, dict):
                        if "canvas" in value and "height" in value["canvas"]:
                            canvas_count += 1
                            break
        
        # If 2+ children have explicit canvas heights, likely a column layout
        return canvas_count >= 2
    
    def enforce_stack_semantics(children):
        """
        Enforce stack semantics: all children must be 100% x 100% to overlay properly.
        """
        for child in children:
            if isinstance(child, dict):
                child["width"] = "100%"
                child["height"] = "100%"
        print(f"  ✓ Stack: enforced width=100%, height=100% for all children")
    
    def enforce_column_semantics(children):
        """
        Enforce column semantics: heights should be properly distributed.
        """
        if not children:
            return
        
        # Check if all children have percentage heights
        percentage_heights = []
        has_non_percentage = False
        
        for child in children:
            if isinstance(child, dict):
                height = child.get("height")
                if height is None:
                    percentage_heights.append(None)
                elif isinstance(height, str) and height.endswith('%'):
                    try:
                        percentage_heights.append(float(height[:-1]))
                    except ValueError:
                        has_non_percentage = True
                        break
                else:
                    # Pixel value or other format
                    has_non_percentage = True
                    break
        
        # If any non-percentage values or missing heights, redistribute
        if has_non_percentage or None in percentage_heights:
            height_percent = round(100 / len(children), 2)
            for child in children:
                if isinstance(child, dict):
                    child["height"] = f"{height_percent}%"
            print(f"  ⚠️  Column: redistributed heights evenly ({height_percent}% each)")
        else:
            # All percentages - check if they sum to ~100%
            total = sum(percentage_heights)
            if total < 95 or total > 105:
                height_percent = round(100 / len(children), 2)
                for child in children:
                    if isinstance(child, dict):
                        child["height"] = f"{height_percent}%"
                print(f"  ⚠️  Column: heights sum to {total}%, redistributed to {height_percent}% each")
            else:
                print(f"  ✓ Column: heights properly distributed (sum={total}%)")
    
    def enforce_row_semantics(children):
        """
        Enforce row semantics: widths should be properly distributed.
        """
        if not children:
            return
        
        # Check if all children have percentage widths
        percentage_widths = []
        has_non_percentage = False
        
        for child in children:
            if isinstance(child, dict):
                width = child.get("width")
                if width is None:
                    percentage_widths.append(None)
                elif isinstance(width, str) and width.endswith('%'):
                    try:
                        percentage_widths.append(float(width[:-1]))
                    except ValueError:
                        has_non_percentage = True
                        break
                else:
                    # Pixel value or other format
                    has_non_percentage = True
                    break
        
        # If any non-percentage values or missing widths, redistribute
        if has_non_percentage or None in percentage_widths:
            width_percent = round(100 / len(children), 2)
            for child in children:
                if isinstance(child, dict):
                    child["width"] = f"{width_percent}%"
            print(f"  ⚠️  Row: redistributed widths evenly ({width_percent}% each)")
        else:
            # All percentages - check if they sum to ~100%
            total = sum(percentage_widths)
            if total < 95 or total > 105:
                width_percent = round(100 / len(children), 2)
                for child in children:
                    if isinstance(child, dict):
                        child["width"] = f"{width_percent}%"
                print(f"  ⚠️  Row: widths sum to {total}%, redistributed to {width_percent}% each")
            else:
                print(f"  ✓ Row: widths properly distributed (sum={total}%)")
    
    def process_node(node, parent_context=None):
        """Recursively process each node in the JSON tree"""
        
        if not isinstance(node, dict):
            return node
        
        processed = {}
        
        for key, value in node.items():
            # Check if this is a canvas_N key
            if key.startswith("canvas_") and isinstance(value, dict):
                if "canvas" in value and "layers" in value:
                    # Flatten the structure and sanitize layers
                    processed["canvas"] = value["canvas"]
                    processed["layers"] = [sanitize_layer(layer) for layer in value.get("layers", [])]
                else:
                    processed[key] = process_node(value, parent_context)
            
            # Handle stack with fallback conversion
            elif key == "stack" and isinstance(value, dict):
                # Check if this should be a column instead
                if should_convert_stack_to_column(value):
                    print("⚠️  Auto-converting 'stack' → 'column' (detected vertical layout pattern)")
                    layout_context = {"type": "column"}
                    processed["column"] = process_node(value, layout_context)
                else:
                    layout_context = {"type": "stack"}
                    processed[key] = process_node(value, layout_context)
            
            # Handle other layout containers
            elif key in ["column", "row"] and isinstance(value, dict):
                layout_context = {"type": key}
                processed[key] = process_node(value, layout_context)
            
            # Handle children arrays
            elif key == "children" and isinstance(value, list):
                processed[key] = []
                num_children = len(value)
                
                for child in value:
                    processed_child = process_node(child, parent_context)
                    processed[key].append(processed_child)
                
                # Enforce semantic constraints AFTER processing all children
                if parent_context:
                    layout_type = parent_context.get("type")
                    
                    if layout_type == "stack":
                        print(f"Enforcing stack semantics for {num_children} children:")
                        enforce_stack_semantics(processed[key])
                    
                    elif layout_type == "column":
                        print(f"Enforcing column semantics for {num_children} children:")
                        enforce_column_semantics(processed[key])
                    
                    elif layout_type == "row":
                        print(f"Enforcing row semantics for {num_children} children:")
                        enforce_row_semantics(processed[key])
            
            # Sanitize layers array
            elif key == "layers" and isinstance(value, list):
                processed[key] = [sanitize_layer(layer) for layer in value]
            
            # Handle container
            elif key == "container" and isinstance(value, dict):
                processed[key] = process_node(value, parent_context)
            
            # Keep all other keys as-is
            else:
                if isinstance(value, dict):
                    processed[key] = process_node(value, parent_context)
                elif isinstance(value, list):
                    processed[key] = [process_node(item, parent_context) if isinstance(item, dict) else item for item in value]
                else:
                    processed[key] = value
        
        return processed
    
    # ==================== Main Translation Logic ====================
    
    print(f"\n{'='*60}")
    print(f"Translating for phase: {phase}")
    print(f"{'='*60}\n")
    
    # Phase-specific preprocessing
    if phase == "layout":
        print("Phase: LAYOUT - Adding placeholder canvases for visualization...")
        # Add placeholder canvases to make structure renderable
        preprocessed = inject_placeholder_canvases(llm_output)
    
    elif phase in ["canvas", "background", "assets"]:
        print(f"Phase: {phase.upper()} - Ensuring proper canvas structure...")
        # Ensure all canvas_N have proper structure
        preprocessed = ensure_canvas_structure(llm_output)
    
    else:
        print(f"⚠️  Unknown phase: {phase}, using default processing")
        preprocessed = llm_output
    
    # Main translation process
    print("\nProcessing structure and enforcing semantics...")
    result = process_node(preprocessed)
    
    print(f"\n{'='*60}")
    print(f"Translation complete for phase: {phase}")
    print(f"{'='*60}\n")
    
    return result
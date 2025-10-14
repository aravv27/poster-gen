def translate_canvas_numbering(llm_output: dict) -> dict:
    """
    Translate LLM output with canvas_N numbering to render engine format.
    
    Features:
    1. Unwraps canvas_N keys and flattens structure
    2. Auto-converts stack → column when detecting vertical layout pattern
    3. Adds appropriate width/height constraints based on layout type
    4. Sanitizes dimension values (removes 'px' suffix)
    """
    
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
                    
                    # Add dimension constraints based on parent layout type
                    if isinstance(processed_child, dict) and parent_context:
                        layout_type = parent_context.get("type")
                        
                        if layout_type == "column":
                            # Column: distribute height, keep width
                            if "height" not in processed_child:
                                height_percent = round(100 / num_children, 2)
                                processed_child["height"] = f"{height_percent}%"
                        
                        elif layout_type == "row":
                            # Row: distribute width, keep height
                            if "width" not in processed_child:
                                width_percent = round(100 / num_children, 2)
                                processed_child["width"] = f"{width_percent}%"
                        
                        elif layout_type == "stack":
                            # Stack: all children fill 100% (layered on top)
                            if "width" not in processed_child:
                                processed_child["width"] = "100%"
                            if "height" not in processed_child:
                                processed_child["height"] = "100%"
                    
                    processed[key].append(processed_child)
            
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
    
    return process_node(llm_output)

# Test with your example
if __name__ == "__main__":
    import json
    
    # Your LLM output with stack (should be column)
    llm_output = {
  "container": {
    "width": 1920,
    "height": 1080,
    "stack": {
      "children": [
        {
          "canvas_1": {
            "canvas": {
              "width": 1920,
              "height": 216,
              "background": "#19202e"
            },
            "layers": [
              {
                "type": "gradient",
                "gradient_type": "linear",
                "colors": [
                  "#19202e",
                  "#232946"
                ],
                "angle": 90,
                "opacity": 1.0,
                "anchor": "top-left",
                "width": "1920px",
                "height": "216px"
              },
              {
                "type": "shape",
                "shape": "ellipse",
                "color": "#232946",
                "x": "0",
                "y": "0",
                "width": "1920",
                "height": "216",
                "anchor": "top-left",
                "opacity": 0.7,
                "blur": 100
              }
            ]
          },
          "width": "100%"
        },
        {
          "canvas_2": {
            "canvas": {
              "width": 1920,
              "height": 216,
              "background": "#232946"
            },
            "layers": [
              {
                "type": "gradient",
                "gradient_type": "radial",
                "x": "70%",
                "y": "30%",
                "opacity": 0.7,
                "anchor": "top-left",
                "colors": [
                  "#3066be",
                  "#19202e"
                ],
                "width": "100%",
                "height": "100%"
              },
              {
                "type": "shape",
                "shape": "ellipse",
                "color": "#3066be",
                "x": "-100",
                "y": "50",
                "width": "800",
                "height": "150",
                "anchor": "top-left",
                "opacity": 0.4,
                "blur": 120
              }
            ]
          },
          "width": "100%"
        },
        {
          "canvas_3": {
            "canvas": {
              "width": 1920,
              "height": 216,
              "background": "#3066be"
            },
            "layers": [
              {
                "type": "gradient",
                "gradient_type": "shape_blur",
                "colors": [
                  "#6fd1fb",
                  "#3066be"
                ],
                "shape_gradient_type": "linear",
                "shape": "ellipse",
                "shape_x": "20%",
                "shape_y": "20%",
                "shape_width": "60%",
                "shape_height": "60%",
                "blur_radius": 50,
                "opacity": 0.5
              }
            ]
          },
          "width": "100%"
        },
        {
          "canvas_4": {
            "canvas": {
              "width": 1920,
              "height": 216,
              "background": "#9a89d9"
            },
            "layers": [
              {
                
                  "type": "gradient",
                  "gradient_type": "mesh",
                  "mesh_points": [
                    {
                      "y": "0%",
                      "x": "0%",
                      "color": "#232946"
                    },
                    {
                      "color": "#3066be",
                      "y": "0%",
                      "x": "100%"
                    },
                    {
                      "y": "100%",
                      "x": "0%",
                      "color": "#9a89d9"
                    },
                    {
                      "y": "100%",
                      "color": "#19202e",
                      "x": "100%"
                    },
                    {
                      "y": "50%",
                      "color": "#6fd1fb",
                      "x": "50%"
                    }
                  ],
                  "opacity": 0.9
                
              }
            ]
          },
          "width": "100%"
        },
        {
          "canvas_5": {
            "canvas": {
              "width": 1920,
              "height": 216,
              "background": "#6fd1fb"
            },
            "layers": [
              {
                "type": "gradient",
                "gradient_type": "linear",
                "colors": [
                  "#19202e",
                  "transparent"
                ],
                "angle": 45,
                "opacity": 0.4,
                "anchor": "top-left",
                "width": "1920px",
                "height": "216px"
              }
            ]
          },
          "width": "100%"
        }
      ]
    }
  }
}
    
    result = translate_canvas_numbering(llm_output)
    print(json.dumps(result, indent=2))
from typing import List, Optional, Dict, Any, Union
import json,re
class Tools:
    @staticmethod
    def generate_layout(layout_string: str) -> Dict[str, Any]:
        def parse_layout(layout_str: str) -> Dict[str, Any]:
            canvas_counter = [1]  # Use list to maintain reference in nested functions
            
            # Remove all whitespace for easier parsing
            layout_str = re.sub(r'\s+', '', layout_str)
            
            # Parse the root container
            container_match = re.match(r'container\((\d+)x(\d+)\)\[(.*)\]$', layout_str)
            if not container_match:
                raise ValueError("Invalid layout string format. Expected: container(widthxheight)[...]")
            
            width = int(container_match.group(1))
            height = int(container_match.group(2))
            content = container_match.group(3)
            
            def parse_layout_element(content: str) -> Dict[str, Any]:
                """Parse a single layout element (column, row, stack, or placeholder)"""
                
                # Check for placeholder
                placeholder_match = re.match(r'placeholder\(([^)]*)\)$', content)
                if placeholder_match:
                    size_spec = placeholder_match.group(1)
                    result = {f"canvas_{canvas_counter[0]}": "PLACEHOLDER"}
                    canvas_counter[0] += 1
                    
                    # Add size specification if provided
                    if size_spec:
                        if 'x' in size_spec:
                            # Dimension format
                            w, h = size_spec.split('x')
                            result["width"] = int(w)
                            result["height"] = int(h)
                        elif size_spec.endswith('%'):
                            # Percentage format
                            result["size"] = size_spec
                        else:
                            # Assume it's a flex value or other size
                            result["size"] = size_spec
                    
                    return result
                
                # Check for column, row, or stack
                layout_types = ['column', 'row', 'stack']
                for layout_type in layout_types:
                    pattern = rf'{layout_type}(?:\(([^)]*)\))?\[(.*)\]$'
                    match = re.match(pattern, content)
                    if match:
                        size_spec = match.group(1)
                        children_content = match.group(2)
                        
                        # Parse children
                        children = parse_children(children_content)
                        
                        result = {
                            layout_type: {
                                "children": children
                            }
                        }
                        
                        # Add size specification if provided
                        if size_spec:
                            if size_spec.endswith('%'):
                                result["size"] = size_spec
                        
                        return result
                
                raise ValueError(f"Could not parse layout element: {content}")
            
            def parse_children(children_content: str) -> List[Dict[str, Any]]:
                """Parse children content, splitting by commas at the correct nesting level"""
                
                if not children_content:
                    return []
                
                children = []
                current_child = ""
                bracket_depth = 0
                paren_depth = 0
                
                i = 0
                while i < len(children_content):
                    char = children_content[i]
                    
                    if char == '[':
                        bracket_depth += 1
                    elif char == ']':
                        bracket_depth -= 1
                    elif char == '(':
                        paren_depth += 1
                    elif char == ')':
                        paren_depth -= 1
                    elif char == ',' and bracket_depth == 0 and paren_depth == 0:
                        # Found a separator at top level
                        if current_child.strip():
                            child_data = parse_layout_element(current_child.strip())
                            children.append(child_data)
                        current_child = ""
                        i += 1
                        continue
                    
                    current_child += char
                    i += 1
                
                # Add the last child
                if current_child.strip():
                    child_data = parse_layout_element(current_child.strip())
                    children.append(child_data)
                
                return children
            
            def apply_size_context(layout_json: Dict[str, Any], parent_type: str = None) -> Dict[str, Any]:
                """Apply size specifications based on context (width for rows, height for columns)"""
                
                def process_node(node, parent_layout_type=None):
                    if isinstance(node, dict):
                        new_node = {}
                        for key, value in node.items():
                            if key == "size":
                                # Convert generic "size" to width/height based on parent context
                                if parent_layout_type == "row":
                                    new_node["width"] = value
                                elif parent_layout_type == "column":
                                    new_node["height"] = value
                                else:
                                    # For stack or unknown context, default to width
                                    new_node["width"] = value
                            elif key in ["column", "row", "stack"]:
                                # Process layout containers
                                new_node[key] = process_node(value, key)
                            elif key == "children" and isinstance(value, list):
                                # Process children with current layout type as parent
                                new_node[key] = [process_node(child, parent_layout_type) for child in value]
                            else:
                                new_node[key] = process_node(value, parent_layout_type)
                        return new_node
                    elif isinstance(node, list):
                        return [process_node(item, parent_layout_type) for item in node]
                    else:
                        return node
                
                return process_node(layout_json)
            
            # Parse the content inside container
            child_layout = parse_layout_element(content)
            
            # Create the full structure
            result = {
                "container": {
                    "width": width,
                    "height": height,
                    **child_layout
                }
            }
            
            # Apply size context
            formatted_result = apply_size_context(result)
            return formatted_result
        
        try:
            return parse_layout(layout_string)
        except Exception as e:
            raise ValueError(f"Error parsing layout string: {str(e)}")

    @staticmethod
    def generate_canvas(width:int,height:int,background = "#000000"):
        canvas = {"width":width,"height":height,"background":background}
        return {
        "width": width,
        "height": height,
        "background": background
    }
    
    @staticmethod
    def generate_radial_gradient(
        colors: List[str] = None,
        stops: Optional[List[float]] = None,
        start_color: Optional[str] = None,
        end_color: Optional[str] = None,
        x: Union[int, str] = "50%",
        y: Union[int, str] = "50%",
        width: Optional[Union[int, str]] = None,
        height: Optional[Union[int, str]] = None,
        opacity: float = 1.0,
        anchor: str = "top-left"
    ) -> Dict[str, Any]:
        gradient = {
            "type": "gradient",
            "gradient_type": "radial",
            "x": x,
            "y": y,
            "opacity": opacity,
            "anchor": anchor
        }
        
        if colors:
            gradient["colors"] = colors
            if stops:
                gradient["stops"] = stops
        elif start_color and end_color:
            gradient["start_color"] = start_color
            gradient["end_color"] = end_color
        if width:
            gradient["width"] = width
        if height:
            gradient["height"] = height
            
        return gradient
    
    @staticmethod
    def generate_linear_gradient(
        colors: List[str],
        stops: Optional[List[float]] = None,
        angle: float = 0,
        opacity: float = 1.0,
        width: Optional[Union[int, str]] = None,
        height: Optional[Union[int, str]] = None,
        anchor: str = "top-left"
    ) -> Dict[str, Any]:
        gradient = {
            "type": "gradient",
            "gradient_type": "linear",
            "colors": colors,
            "angle": angle,
            "opacity": opacity,
            "anchor": anchor
        }
        
        if stops:
            gradient["stops"] = stops
        if width:
            gradient["width"] = width
        if height:
            gradient["height"] = height
            
        return gradient
    
    @staticmethod
    def generate_mesh_gradient(
        mesh_points: List[Dict[str, Union[str, int, float]]],
        opacity: float = 1.0
    ) -> Dict[str, Any]:
        return {
            "mesh_gradient": {
                "type": "gradient",
                "gradient_type": "mesh",
                "mesh_points": mesh_points,
                "opacity": opacity
            }
        }
    
    @staticmethod
    def generate_shape_blur_gradient(
        colors: List[str],
        stops: Optional[List[float]] = None,
        angle: Optional[float] = None,
        shape_gradient_type: str = "linear",
        shape: str = "ellipse",
        shape_x: Union[int, str] = "0%",
        shape_y: Union[int, str] = "0%",
        shape_width: Union[int, str] = "100%",
        shape_height: Union[int, str] = "100%",
        blur_radius: int = 20,
        opacity: float = 1.0
    ) -> Dict[str, Any]:
        gradient = {
            "type": "gradient",
            "gradient_type": "shape_blur",
            "colors": colors,
            "shape_gradient_type": shape_gradient_type,
            "shape": shape,
            "shape_x": shape_x,
            "shape_y": shape_y,
            "shape_width": shape_width,
            "shape_height": shape_height,
            "blur_radius": blur_radius,
            "opacity": opacity
        }
        
        if stops:
            gradient["stops"] = stops
        if angle is not None:
            gradient["angle"] = angle
            
        return gradient
    
    @staticmethod
    def generate_color_overlay(
        color: str,
        width: Optional[Union[int, str]] = None,
        height: Optional[Union[int, str]] = None,
        x: Union[int, str] = 0,
        y: Union[int, str] = 0,
        anchor: str = "top-left",
        opacity: float = 1.0,
        blur: int = 0
    ) -> Dict[str, Any]:
        overlay = {
            "type": "color_overlay",
            "color": color,
            "x": x,
            "y": y,
            "anchor": anchor,
            "opacity": opacity,
            "blur": blur
        }
        
        if width:
            overlay["width"] = width
        if height:
            overlay["height"] = height
            
        return overlay
    
    @staticmethod
    def generate_image_layer(
        src: str,
        x: Union[int, str] = 0,
        y: Union[int, str] = 0,
        anchor: str = "top-left",
        width: Optional[Union[int, str]] = None,
        height: Optional[Union[int, str]] = None,
        opacity: float = 1.0,
        angle: float = 0,
        flip: bool = False,
        flop: bool = False,
        filters: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an image layer.
        
        Args:
            src: Path to the image file
            x: X position (pixels or percentage)
            y: Y position (pixels or percentage)
            anchor: Anchor point for positioning ('top-left', 'center', 'bottom-right', etc.)
            width: Image width (pixels or percentage)
            height: Image height (pixels or percentage)
            opacity: Opacity (0.0 to 1.0)
            angle: Rotation angle in degrees
            flip: Flip vertically
            flop: Flip horizontally
            filters: List of filter dictionaries
                - {"type": "gaussian_blur", "radius": 5}
                - {"type": "grayscale"}
                - {"type": "brightness_contrast", "brightness": 1.2, "contrast": 1.1}
        """
        layer = {
            "type": "image",
            "src": src,
            "x": x,
            "y": y,
            "anchor": anchor,
            "opacity": opacity
        }
        
        if width is not None:
            layer["width"] = width
        if height is not None:
            layer["height"] = height
        if angle != 0:
            layer["angle"] = angle
        if flip:
            layer["flip"] = flip
        if flop:
            layer["flop"] = flop
        if filters:
            layer["filters"] = filters
            
        return layer
    
    @staticmethod
    def generate_text_layer(
        text: str,
        x: Union[int, str] = 0,
        y: Union[int, str] = 0,
        anchor: str = "top-left",
        font: Optional[str] = None,
        size: int = 32,
        color: str = "#ffffff",
        align: str = "left",
        opacity: float = 1.0,
        weight: str = "normal",
        stroke_color: Optional[str] = None,
        stroke_width: int = 0,
        line_height: float = 1.0,
        letter_spacing: int = 0,
        transform: Optional[str] = None,
        shadow: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a text layer.
        
        Args:
            text: Text content (use \\n for line breaks)
            x: X position (pixels or percentage)
            y: Y position (pixels or percentage)
            anchor: Anchor point ('top-left', 'center', 'bottom-right', etc.)
            font: Path to font file
            size: Font size in pixels
            color: Text color (hex)
            align: Text alignment ('left', 'center', 'right')
            opacity: Opacity (0.0 to 1.0)
            weight: Font weight ('normal', 'bold')
            stroke_color: Stroke/outline color (hex)
            stroke_width: Stroke width in pixels
            line_height: Line height multiplier
            letter_spacing: Extra spacing between letters in pixels
            transform: Text transform ('uppercase', 'lowercase', 'capitalize')
            shadow: Shadow dict with keys: offset_x, offset_y, color, opacity
        """
        layer = {
            "type": "text",
            "text": text,
            "x": x,
            "y": y,
            "anchor": anchor,
            "size": size,
            "color": color,
            "align": align,
            "opacity": opacity,
            "weight": weight,
            "line_height": line_height,
            "letter_spacing": letter_spacing
        }
        
        if font:
            layer["font"] = font
        if stroke_color:
            layer["stroke_color"] = stroke_color
        if stroke_width > 0:
            layer["stroke_width"] = stroke_width
        if transform:
            layer["transform"] = transform
        if shadow:
            layer["shadow"] = shadow
            
        return layer
    
    @staticmethod
    def generate_ellipse(
        color: str,
        x: Union[int, str] = 0,
        y: Union[int, str] = 0,
        width: Union[int, str] = 100,
        height: Union[int, str] = 100,
        anchor: str = "top-left",
        opacity: float = 1.0,
        blur: int = 0
    ) -> Dict[str, Any]:
        """
        Generate an ellipse shape layer.
        
        Args:
            color: Fill color (hex)
            x: X position (pixels or percentage)
            y: Y position (pixels or percentage)
            width: Ellipse width (pixels or percentage)
            height: Ellipse height (pixels or percentage)
            anchor: Anchor point for positioning
            opacity: Opacity (0.0 to 1.0)
            blur: Blur radius in pixels
        """
        return {
            
                "type": "shape",
                "shape": "ellipse",
                "color": color,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "anchor": anchor,
                "opacity": opacity,
                "blur": blur
            
        }
    
    @staticmethod
    def generate_polygon(
        color: str,
        points: List[List[Union[int, str]]],
        opacity: float = 1.0,
        blur: int = 0
    ) -> Dict[str, Any]:
        """
        Generate a polygon shape layer.
        
        Args:
            color: Fill color (hex)
            points: List of [x, y] coordinates (pixels or percentages)
            opacity: Opacity (0.0 to 1.0)
            blur: Blur radius in pixels
            
        Example:
            points = [[0, 0], [100, 0], [50, 100]]  # Triangle
            points = [["10%", "10%"], ["90%", "10%"], ["50%", "90%"]]  # Triangle with percentages
        """
        return {
            
                "type": "shape",
                "shape": "polygon",
                "color": color,
                "points": points,
                "opacity": opacity,
                "blur": blur
            
        }




from typing import List, Optional, Dict, Any, Union
import json
class Tools:
    @staticmethod
    def generate_canvas(width:int,height:int,background = "#000000"):
        canvas = {"width":width,"height":height,"background":background}
        return {"canvas":canvas}
    
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
            
        return {"radial_gradient": gradient}
    
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
            
        return {"linear_gradient": gradient}
    
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
            
        return {"shape_blur_gradient": gradient}
    
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
            
        return {"color_overlay": overlay}


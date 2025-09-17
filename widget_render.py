import json
from PIL import Image
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional

from utils import hex_to_rgba
from background import (
    draw_radial_gradient,
    draw_linear_gradient,
    draw_mesh_gradient,
    draw_shape_blur_gradient,
    draw_color_overlay,
    draw_spray_noise
)
from assets import (
    draw_ellipse,
    draw_polygon,
    draw_image_layer,
    draw_text_layer
)


def draw_layer(base, layer, width, height):
    t = layer['type']
    if t == 'gradient' and layer.get('gradient_type') == 'radial':
        draw_radial_gradient(base, layer, width, height)
    elif t == "gradient" and layer.get('gradient_type') == 'linear':
        draw_linear_gradient(base,layer,width,height)
    elif t == "gradient" and layer.get('gradient_type') == 'mesh':
        draw_mesh_gradient(base,layer,width,height)
    elif t == "gradient" and layer.get('gradient_type') == 'shape_blur':
        draw_shape_blur_gradient(base,layer,width,height)
    elif t == 'color_overlay':
        draw_color_overlay(base, layer, width, height)
    elif t == 'shape' and layer.get('shape', None) == 'ellipse':
        draw_ellipse(base, layer, width, height)
    elif t == 'shape' and layer.get('shape', None) == 'polygon':
        draw_polygon(base, layer, width, height)
    elif t == "spray_noise":
        draw_spray_noise(base, layer, width, height)
    elif t == "image":
        draw_image_layer(base,layer,width,height)
    elif t == "text":
        draw_text_layer(base,layer,width,height)
    # Add more types as needed


class Widget(ABC):
    """Base widget class"""
    
    def __init__(self, padding: int = 0, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        self.computed_size: Optional[Tuple[int, int]] = None
        self.position: Tuple[int, int] = (0, 0)
        self.padding = padding
        self.bg_color = bg_color
    
    @abstractmethod
    def calculate_size(self) -> Tuple[int, int]:
        """Calculate and return the size of this widget"""
        pass
    
    @abstractmethod
    def render(self, x: int, y: int) -> Image.Image:
        """Render this widget at the given position and return PIL Image"""
        pass

class Canvas(Widget):
    """Canvas widget that renders layers"""
    
    def __init__(self, canvas_config: Dict, layers: List[Dict], padding: int = 0, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        super().__init__(padding, bg_color)
        self.width = canvas_config['width']
        self.height = canvas_config['height']
        self.background = canvas_config.get('background', '#000000')
        self.layers = layers
    
    def calculate_size(self) -> Tuple[int, int]:
        # Canvas size includes padding
        self.computed_size = (self.width + 2 * self.padding, self.height + 2 * self.padding)
        return self.computed_size
    
    def render(self, x: int, y: int) -> Image.Image:
        """Render canvas with padding and background"""
        total_width, total_height = self.computed_size
        
        # Create full image with padding
        full_image = Image.new("RGBA", (total_width, total_height), self.bg_color)
        
        # Create canvas content
        canvas_content = Image.new("RGBA", (self.width, self.height), hex_to_rgba(self.background))
        
        # Apply all layers to the canvas content
        for layer in self.layers:
            draw_layer(canvas_content, layer, self.width, self.height)
        
        # Paste canvas content into full image with padding offset
        full_image.paste(canvas_content, (self.padding, self.padding))
        
        return full_image

class Container(Widget):
    """Container widget with single child"""
    
    def __init__(self, child: Widget, padding: int = 0, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        super().__init__(padding, bg_color)
        self.child = child
    
    def calculate_size(self) -> Tuple[int, int]:
        # Container size = child size + padding
        child_width, child_height = self.child.calculate_size()
        self.computed_size = (child_width + 2 * self.padding, child_height + 2 * self.padding)
        return self.computed_size
    
    def render(self, x: int, y: int) -> Image.Image:
        """Render container with background and child"""
        width, height = self.computed_size
        
        # Create container background
        container_image = Image.new("RGBA", (width, height), self.bg_color)
        
        # Render child with padding offset
        child_image = self.child.render(0, 0)
        
        # Paste child into container with padding
        if child_image.mode == 'RGBA':
            container_image.paste(child_image, (self.padding, self.padding), child_image)
        else:
            container_image.paste(child_image, (self.padding, self.padding))
        
        return container_image

class Row(Widget):
    """Row widget that arranges children horizontally"""
    
    def __init__(self, children: List[Widget], padding: int = 0, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        super().__init__(padding, bg_color)
        self.children = children
    
    def calculate_size(self) -> Tuple[int, int]:
        if not self.children:
            self.computed_size = (2 * self.padding, 2 * self.padding)
            return self.computed_size
        
        total_width = 0
        max_height = 0
        
        for child in self.children:
            child_width, child_height = child.calculate_size()
            total_width += child_width
            max_height = max(max_height, child_height)
        
        # Add padding to the total size
        self.computed_size = (total_width + 2 * self.padding, max_height + 2 * self.padding)
        print(f"Row size calculated: {self.computed_size}, children: {len(self.children)}, padding: {self.padding}")  # Debug
        return self.computed_size
    
    def render(self, x: int, y: int) -> Image.Image:
        """Render row with background and children positioned horizontally"""
        width, height = self.computed_size
        
        # Create row background
        row_image = Image.new("RGBA", (width, height), self.bg_color)
        
        # Position children horizontally within padding area
        current_x = self.padding
        for child in self.children:
            child_image = child.render(0, 0)
            child_width, child_height = child.computed_size
            
            # Paste child image at current position (vertically centered in padding area)
            y_offset = self.padding + (height - 2 * self.padding - child_height) // 2
            if child_image.mode == 'RGBA':
                row_image.paste(child_image, (current_x, max(self.padding, y_offset)), child_image)
            else:
                row_image.paste(child_image, (current_x, max(self.padding, y_offset)))
            
            current_x += child_width
        
        return row_image

class Column(Widget):
    """Column widget that arranges children vertically"""
    
    def __init__(self, children: List[Widget], padding: int = 0, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        super().__init__(padding, bg_color)
        self.children = children
    
    def calculate_size(self) -> Tuple[int, int]:
        if not self.children:
            self.computed_size = (2 * self.padding, 2 * self.padding)
            return self.computed_size
        
        max_width = 0
        total_height = 0
        
        for child in self.children:
            child_width, child_height = child.calculate_size()
            max_width = max(max_width, child_width)
            total_height += child_height
        
        # Add padding to the total size
        self.computed_size = (max_width + 2 * self.padding, total_height + 2 * self.padding)
        return self.computed_size
    
    def render(self, x: int, y: int) -> Image.Image:
        """Render column with background and children positioned vertically"""
        width, height = self.computed_size
        
        # Create column background
        column_image = Image.new("RGBA", (width, height), self.bg_color)
        
        # Position children vertically within padding area
        current_y = self.padding
        for child in self.children:
            child_image = child.render(0, 0)
            child_width, child_height = child.computed_size
            
            # Paste child image at current position (horizontally centered in padding area)
            x_offset = self.padding + (width - 2 * self.padding - child_width) // 2
            if child_image.mode == 'RGBA':
                column_image.paste(child_image, (max(self.padding, x_offset), current_y), child_image)
            else:
                column_image.paste(child_image, (max(self.padding, x_offset), current_y))
            
            current_y += child_height
        
        return column_image

class WidgetTreeParser:
    """Parser to convert JSON to widget tree"""
    
    @staticmethod
    def parse(data: Dict) -> Widget:
        """Parse JSON structure into widget tree"""
        return WidgetTreeParser._parse_node(data)
    
    @staticmethod
    def _parse_node(node: Dict) -> Widget:
        """Recursively parse a node in the JSON structure"""
        
        print(f"Parsing node: {list(node.keys())}")  # Debug print
        
        # Handle canvas (leaf node)
        if 'canvas' in node:
            canvas_config = node['canvas']
            layers = node.get('layers', [])
            padding = node.get('padding', 0)
            bg_color = node.get('bg_color', (0, 0, 0, 0))
            print(f"Creating Canvas: {canvas_config['width']}x{canvas_config['height']}, layers: {len(layers)}, padding: {padding}")
            return Canvas(canvas_config, layers, padding, bg_color)
        
        # Handle child wrapper
        if 'child' in node:
            print("Parsing child wrapper")
            return WidgetTreeParser._parse_node(node['child'])
        
        # Handle container
        if 'container' in node:
            container_data = node['container']
            padding = node.get('padding', 0)
            bg_color = node.get('bg_color', (0, 0, 0, 0))
            print(f"Creating Container with padding: {padding}")
            child = WidgetTreeParser._parse_node(container_data)
            return Container(child, padding, bg_color)
        
        # Handle row
        if 'row' in node:
            row_data = node['row']
            children = []
            padding = node.get('padding', 0)
            bg_color = node.get('bg_color', (0, 0, 0, 0))
            print(f"Creating Row with data keys: {list(row_data.keys())}, padding: {padding}")
            
            # Check if row has explicit children array
            if 'children' in row_data:
                print("Found children array in row")
                for i, child_data in enumerate(row_data['children']):
                    print(f"Parsing row child {i}: {list(child_data.keys())}")
                    child_widget = WidgetTreeParser._parse_node(child_data)
                    children.append(child_widget)
            else:
                # Parse all children of the row (old format)
                for key, value in row_data.items():
                    if key not in ['children', 'padding', 'bg_color']:  # Skip properties
                        print(f"Parsing row child: {key}")
                        child_widget = WidgetTreeParser._parse_node({key: value})
                        children.append(child_widget)
            
            print(f"Row created with {len(children)} children")
            return Row(children, padding, bg_color)
        
        # Handle column
        if 'column' in node:
            column_data = node['column']
            children = []
            padding = node.get('padding', 0)
            bg_color = node.get('bg_color', (0, 0, 0, 0))
            print(f"Creating Column with data keys: {list(column_data.keys())}, padding: {padding}")
            
            # Check if column has explicit children array
            if 'children' in column_data:
                print("Found children array in column")
                for i, child_data in enumerate(column_data['children']):
                    print(f"Parsing column child {i}: {list(child_data.keys())}")
                    child_widget = WidgetTreeParser._parse_node(child_data)
                    children.append(child_widget)
            else:
                # Parse all children of the column (old format)
                for key, value in column_data.items():
                    if key not in ['children', 'padding', 'bg_color']:  # Skip properties
                        print(f"Parsing column child: {key}")
                        child_widget = WidgetTreeParser._parse_node({key: value})
                        children.append(child_widget)
            
            print(f"Column created with {len(children)} children")
            return Column(children, padding, bg_color)
        
        raise ValueError(f"Unknown node structure: {node}")

class WidgetTreeRenderer:
    """Main renderer for widget trees"""
    
    def __init__(self):
        pass
    
    def render_from_json(self, json_data: Dict, output_path: str = "widget_output.png"):
        """Render widget tree from JSON and save to file"""
        # Parse JSON to widget tree
        root_widget = WidgetTreeParser.parse(json_data)
        
        # Calculate sizes (bottom-up)
        root_widget.calculate_size()
        
        # Render the tree (top-down)
        final_image = root_widget.render(0, 0)
        
        # Convert to RGB and save
        if final_image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', final_image.size, (255, 255, 255))
            background.paste(final_image, mask=final_image.split()[3])  # Use alpha as mask
            final_image = background
        
        final_image.save(output_path, quality=95)
        print(f"Widget tree rendered and saved as {output_path}")
        
        return final_image

# Example usage
if __name__ == "__main__":
    # Fixed JSON structure - use array for multiple children
    example_json = {
        "container": {
            "padding":10,
            "bg_color":(220,212,123,234),
            "row": {
                "children": [
                    {
                        "column": {
                            "child": {
                                "canvas": {
                                    "width": 1920,
                                    "height": 1080,
                                    "background": "#08106E"
                                },
                                "layers": [
                                    {
                                        "type": "color_overlay",
                                        "color": "#08106E",
                                        "x": "0%",
                                        "y": "0%",
                                        "width": "100%",
                                        "height": "100%",
                                        "opacity": 0.9,
                                        "blur": 30
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "column": {
                            "child": {
                                "canvas": {
                                    "width": 1911,
                                    "height": 1010,
                                    "background": "#585d97ff"
                                },
                                "layers": [
                                    {
                                        "type": "gradient",
                                        "gradient_type": "radial",
                                        "start_color": "#35E2FC",
                                        "end_color": "#E831DF",
                                        "colors": ["#35E2FC", "#E831DF", "#08106E"],
                                        "stops": [0, 0.7, 1],
                                        "x": "0%",
                                        "y": "100%",
                                        "width": "200%",
                                        "height": "200%",
                                        "opacity": 1,
                                        "anchor": "top-right"
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
    }
    
    # Render the widget tree
    renderer = WidgetTreeRenderer()
    renderer.render_from_json(example_json)
    
    # You can also load from file:
    # with open('widget_config.json', 'r') as f:
    #     config = json.load(f)
    # renderer.render_from_json(config)
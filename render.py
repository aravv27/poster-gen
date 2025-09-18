import json
from PIL import Image
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional, Union

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


def parse_size_value(value: Union[str, int], available_space: int) -> int:
    """Parse size value (int, percentage string) into pixels"""
    if isinstance(value, int):
        return value
    elif isinstance(value, str) and value.endswith('%'):
        percentage = float(value[:-1]) / 100.0
        return int(available_space * percentage)
    else:
        raise ValueError(f"Invalid size value: {value}")


class BoxConstraints:
    """Box constraints for layout"""
    
    def __init__(self, min_width: int = 0, max_width: int = float('inf'), 
                 min_height: int = 0, max_height: int = float('inf')):
        self.min_width = min_width
        self.max_width = max_width if max_width != float('inf') else 999999
        self.min_height = min_height
        self.max_height = max_height if max_height != float('inf') else 999999
    
    def tighten(self, width: int = None, height: int = None) -> 'BoxConstraints':
        """Create tight constraints with fixed dimensions"""
        new_width = width if width is not None else self.max_width
        new_height = height if height is not None else self.max_height
        return BoxConstraints(new_width, new_width, new_height, new_height)
    
    def loosen(self) -> 'BoxConstraints':
        """Create loose constraints (min = 0)"""
        return BoxConstraints(0, self.max_width, 0, self.max_height)
    
    def constrain_width(self, width: int) -> int:
        """Constrain width to bounds"""
        return max(self.min_width, min(self.max_width, width))
    
    def constrain_height(self, height: int) -> int:
        """Constrain height to bounds"""
        return max(self.min_height, min(self.max_height, height))
    
    def constrain(self, width: int, height: int) -> Tuple[int, int]:
        """Constrain both dimensions"""
        return (self.constrain_width(width), self.constrain_height(height))
    
    def deflate(self, padding: int) -> 'BoxConstraints':
        """Reduce constraints by padding"""
        return BoxConstraints(
            max(0, self.min_width - 2 * padding),
            max(0, self.max_width - 2 * padding),
            max(0, self.min_height - 2 * padding),
            max(0, self.max_height - 2 * padding)
        )
    
    @property
    def has_bounded_width(self) -> bool:
        return self.max_width < 999999
    
    @property
    def has_bounded_height(self) -> bool:
        return self.max_height < 999999


class Widget(ABC):
    """Base widget class"""
    
    def __init__(self, padding: int = 0, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 width: Union[int, str, None] = None, height: Union[int, str, None] = None,
                 flex: int = 0, x: Union[int, str, None] = None, y: Union[int, str, None] = None,
                 overflow: str = "visible"):
        self.computed_size: Optional[Tuple[int, int]] = None
        self.position: Tuple[int, int] = (0, 0)
        self.padding = padding
        self.bg_color = bg_color
        self.width = width
        self.height = height
        self.flex = flex
        self.x = x
        self.y = y
        self.overflow = overflow  # "visible" or "clip"
    
    @abstractmethod
    def calculate_size(self, constraints: BoxConstraints) -> Tuple[int, int]:
        """Calculate and return the size of this widget given constraints"""
        pass
    
    @abstractmethod
    def render(self, x: int, y: int, constraints: BoxConstraints) -> Image.Image:
        """Render this widget at the given position and return PIL Image"""
        pass
    
    def _resolve_size(self, constraints: BoxConstraints) -> Tuple[int, int]:
        """Resolve width/height specifications against constraints"""
        # Available space for percentage calculations (excluding padding)
        available_width = constraints.max_width - 2 * self.padding
        available_height = constraints.max_height - 2 * self.padding
        
        # Resolve width
        if self.width is not None:
            if isinstance(self.width, str) and self.width.endswith('%'):
                resolved_width = parse_size_value(self.width, available_width) + 2 * self.padding
            else:
                resolved_width = self.width + 2 * self.padding if isinstance(self.width, int) else self.width
        else:
            resolved_width = None
        
        # Resolve height
        if self.height is not None:
            if isinstance(self.height, str) and self.height.endswith('%'):
                resolved_height = parse_size_value(self.height, available_height) + 2 * self.padding
            else:
                resolved_height = self.height + 2 * self.padding if isinstance(self.height, int) else self.height
        else:
            resolved_height = None
        
        return resolved_width, resolved_height


class Canvas(Widget):
    """Canvas widget that renders layers"""
    
    def __init__(self, canvas_config: Dict, layers: List[Dict], **kwargs):
        super().__init__(**kwargs)
        self.canvas_width = canvas_config['width']
        self.canvas_height = canvas_config['height']
        self.background = canvas_config.get('background', '#000000')
        self.layers = layers
    
    def calculate_size(self, constraints: BoxConstraints) -> Tuple[int, int]:
        # Canvas has fixed content size plus padding
        total_width = self.canvas_width + 2 * self.padding
        total_height = self.canvas_height + 2 * self.padding
        
        self.computed_size = constraints.constrain(total_width, total_height)
        return self.computed_size
    
    def render(self, x: int, y: int, constraints: BoxConstraints) -> Image.Image:
        """Render canvas with padding and background"""
        total_width, total_height = self.computed_size
        
        # Create full image with padding
        full_image = Image.new("RGBA", (total_width, total_height), self.bg_color)
        
        # Create canvas content
        canvas_content = Image.new("RGBA", (self.canvas_width, self.canvas_height), hex_to_rgba(self.background))
        
        # Apply all layers to the canvas content
        for layer in self.layers:
            draw_layer(canvas_content, layer, self.canvas_width, self.canvas_height)
        
        # Paste canvas content into full image with padding offset
        full_image.paste(canvas_content, (self.padding, self.padding))
        
        return full_image


class Container(Widget):
    """Container widget with single child"""
    
    def __init__(self, child: Widget, **kwargs):
        super().__init__(**kwargs)
        self.child = child
    
    def calculate_size(self, constraints: BoxConstraints) -> Tuple[int, int]:
        resolved_width, resolved_height = self._resolve_size(constraints)
        
        if resolved_width is not None and resolved_height is not None:
            # Both dimensions specified
            self.computed_size = constraints.constrain(resolved_width, resolved_height)
        else:
            # Calculate child size with deflated constraints
            child_constraints = constraints.deflate(self.padding)
            child_width, child_height = self.child.calculate_size(child_constraints)
            
            # Use specified dimensions or child size + padding
            final_width = resolved_width if resolved_width is not None else child_width + 2 * self.padding
            final_height = resolved_height if resolved_height is not None else child_height + 2 * self.padding
            
            self.computed_size = constraints.constrain(final_width, final_height)
        
        return self.computed_size
    
    def render(self, x: int, y: int, constraints: BoxConstraints) -> Image.Image:
        """Render container with background and child"""
        width, height = self.computed_size
        
        # Create container background
        container_image = Image.new("RGBA", (width, height), self.bg_color)
        
        # Create constraints for child (available space minus padding)
        child_constraints = BoxConstraints(
            0, width - 2 * self.padding,
            0, height - 2 * self.padding
        )
        
        # Render child with padding offset
        child_image = self.child.render(0, 0, child_constraints)
        
        # Paste child into container with padding
        if child_image.mode == 'RGBA':
            container_image.paste(child_image, (self.padding, self.padding), child_image)
        else:
            container_image.paste(child_image, (self.padding, self.padding))
        
        return container_image


class Row(Widget):
    """Row widget that arranges children horizontally"""
    
    def __init__(self, children: List[Widget], **kwargs):
        super().__init__(**kwargs)
        self.children = children
    
    def calculate_size(self, constraints: BoxConstraints) -> Tuple[int, int]:
        if not self.children:
            self.computed_size = (2 * self.padding, 2 * self.padding)
            return self.computed_size
        
        resolved_width, resolved_height = self._resolve_size(constraints)
        
        # Available space for children (excluding padding)
        available_width = constraints.max_width - 2 * self.padding
        available_height = constraints.max_height - 2 * self.padding
        
        # Calculate flex distribution
        total_flex = sum(child.flex for child in self.children if child.flex > 0)
        fixed_width = 0
        flexible_children = []
        
        # First pass: calculate fixed-size children
        for child in self.children:
            if child.flex == 0:
                # Fixed size child
                child_constraints = BoxConstraints(0, available_width, 0, available_height)
                child_width, child_height = child.calculate_size(child_constraints)
                fixed_width += child_width
            else:
                flexible_children.append(child)
        
        # Second pass: distribute remaining space among flexible children
        remaining_width = max(0, available_width - fixed_width)
        flex_unit = remaining_width / total_flex if total_flex > 0 else 0
        
        total_width = fixed_width
        max_height = 0
        
        for child in flexible_children:
            flex_width = int(flex_unit * child.flex)
            child_constraints = BoxConstraints(flex_width, flex_width, 0, available_height)
            child_width, child_height = child.calculate_size(child_constraints)
            total_width += child_width
            max_height = max(max_height, child_height)
        
        # Calculate max height from all children
        for child in self.children:
            if child.flex == 0:
                child_constraints = BoxConstraints(0, available_width, 0, available_height)
                _, child_height = child.calculate_size(child_constraints)
                max_height = max(max_height, child_height)
        
        # Use specified dimensions or calculated size + padding
        final_width = resolved_width if resolved_width is not None else total_width + 2 * self.padding
        final_height = resolved_height if resolved_height is not None else max_height + 2 * self.padding
        
        self.computed_size = constraints.constrain(final_width, final_height)
        return self.computed_size
    
    def render(self, x: int, y: int, constraints: BoxConstraints) -> Image.Image:
        """Render row with background and children positioned horizontally"""
        width, height = self.computed_size
        
        # Create row background
        row_image = Image.new("RGBA", (width, height), self.bg_color)
        
        if not self.children:
            return row_image
        
        # Available space for children (excluding padding)
        available_width = width - 2 * self.padding
        available_height = height - 2 * self.padding
        
        # Calculate flex distribution (same logic as calculate_size)
        total_flex = sum(child.flex for child in self.children if child.flex > 0)
        fixed_width = 0
        
        # First pass: calculate fixed-size children widths
        child_widths = []
        for child in self.children:
            if child.flex == 0:
                child_constraints = BoxConstraints(0, available_width, 0, available_height)
                child_width, _ = child.calculate_size(child_constraints)
                child_widths.append(child_width)
                fixed_width += child_width
            else:
                child_widths.append(None)  # Will be calculated in second pass
        
        # Second pass: distribute remaining space
        remaining_width = max(0, available_width - fixed_width)
        flex_unit = remaining_width / total_flex if total_flex > 0 else 0
        
        for i, child in enumerate(self.children):
            if child.flex > 0:
                flex_width = int(flex_unit * child.flex)
                child_widths[i] = flex_width
        
        # Position children horizontally within padding area
        current_x = self.padding
        for i, child in enumerate(self.children):
            child_width = child_widths[i]
            child_constraints = BoxConstraints(child_width, child_width, 0, available_height)
            child_image = child.render(0, 0, child_constraints)
            child_actual_width, child_height = child_image.size
            
            # Vertically center child in available space
            y_offset = self.padding + (available_height - child_height) // 2
            y_offset = max(self.padding, y_offset)
            
            if child_image.mode == 'RGBA':
                row_image.paste(child_image, (current_x, y_offset), child_image)
            else:
                row_image.paste(child_image, (current_x, y_offset))
            
            current_x += child_actual_width
        
        return row_image


class Column(Widget):
    """Column widget that arranges children vertically"""
    
    def __init__(self, children: List[Widget], **kwargs):
        super().__init__(**kwargs)
        self.children = children
    
    def calculate_size(self, constraints: BoxConstraints) -> Tuple[int, int]:
        if not self.children:
            self.computed_size = (2 * self.padding, 2 * self.padding)
            return self.computed_size
        
        resolved_width, resolved_height = self._resolve_size(constraints)
        
        # Available space for children (excluding padding)
        available_width = constraints.max_width - 2 * self.padding
        available_height = constraints.max_height - 2 * self.padding
        
        # Calculate flex distribution
        total_flex = sum(child.flex for child in self.children if child.flex > 0)
        fixed_height = 0
        flexible_children = []
        
        # First pass: calculate fixed-size children
        for child in self.children:
            if child.flex == 0:
                # Fixed size child
                child_constraints = BoxConstraints(0, available_width, 0, available_height)
                child_width, child_height = child.calculate_size(child_constraints)
                fixed_height += child_height
            else:
                flexible_children.append(child)
        
        # Second pass: distribute remaining space among flexible children
        remaining_height = max(0, available_height - fixed_height)
        flex_unit = remaining_height / total_flex if total_flex > 0 else 0
        
        total_height = fixed_height
        max_width = 0
        
        for child in flexible_children:
            flex_height = int(flex_unit * child.flex)
            child_constraints = BoxConstraints(0, available_width, flex_height, flex_height)
            child_width, child_height = child.calculate_size(child_constraints)
            total_height += child_height
            max_width = max(max_width, child_width)
        
        # Calculate max width from all children
        for child in self.children:
            if child.flex == 0:
                child_constraints = BoxConstraints(0, available_width, 0, available_height)
                child_width, _ = child.calculate_size(child_constraints)
                max_width = max(max_width, child_width)
        
        # Use specified dimensions or calculated size + padding
        final_width = resolved_width if resolved_width is not None else max_width + 2 * self.padding
        final_height = resolved_height if resolved_height is not None else total_height + 2 * self.padding
        
        self.computed_size = constraints.constrain(final_width, final_height)
        return self.computed_size
    
    def render(self, x: int, y: int, constraints: BoxConstraints) -> Image.Image:
        """Render column with background and children positioned vertically"""
        width, height = self.computed_size
        
        # Create column background
        column_image = Image.new("RGBA", (width, height), self.bg_color)
        
        if not self.children:
            return column_image
        
        # Available space for children (excluding padding)
        available_width = width - 2 * self.padding
        available_height = height - 2 * self.padding
        
        # Calculate flex distribution (same logic as calculate_size)
        total_flex = sum(child.flex for child in self.children if child.flex > 0)
        fixed_height = 0
        
        # First pass: calculate fixed-size children heights
        child_heights = []
        for child in self.children:
            if child.flex == 0:
                child_constraints = BoxConstraints(0, available_width, 0, available_height)
                _, child_height = child.calculate_size(child_constraints)
                child_heights.append(child_height)
                fixed_height += child_height
            else:
                child_heights.append(None)  # Will be calculated in second pass
        
        # Second pass: distribute remaining space
        remaining_height = max(0, available_height - fixed_height)
        flex_unit = remaining_height / total_flex if total_flex > 0 else 0
        
        for i, child in enumerate(self.children):
            if child.flex > 0:
                flex_height = int(flex_unit * child.flex)
                child_heights[i] = flex_height
        
        # Position children vertically within padding area
        current_y = self.padding
        for i, child in enumerate(self.children):
            child_height = child_heights[i]
            child_constraints = BoxConstraints(0, available_width, child_height, child_height)
            child_image = child.render(0, 0, child_constraints)
            child_width, child_actual_height = child_image.size
            
            # Horizontally center child in available space
            x_offset = self.padding + (available_width - child_width) // 2
            x_offset = max(self.padding, x_offset)
            
            if child_image.mode == 'RGBA':
                column_image.paste(child_image, (x_offset, current_y), child_image)
            else:
                column_image.paste(child_image, (x_offset, current_y))
            
            current_y += child_actual_height
        
        return column_image


class Stack(Widget):
    """Stack widget that overlays children with positioning"""
    
    def __init__(self, children: List[Widget], **kwargs):
        super().__init__(**kwargs)
        self.children = children
    
    def calculate_size(self, constraints: BoxConstraints) -> Tuple[int, int]:
        resolved_width, resolved_height = self._resolve_size(constraints)
        
        if resolved_width is not None and resolved_height is not None:
            # Both dimensions specified
            self.computed_size = constraints.constrain(resolved_width, resolved_height)
        else:
            # Calculate the maximum bounds needed by all positioned children
            available_width = constraints.max_width - 2 * self.padding
            available_height = constraints.max_height - 2 * self.padding
            
            max_width = 0
            max_height = 0
            
            for child in self.children:
                child_constraints = BoxConstraints(0, available_width, 0, available_height)
                child_width, child_height = child.calculate_size(child_constraints)
                
                # Calculate child position
                child_x = 0
                child_y = 0
                
                if child.x is not None:
                    if isinstance(child.x, str) and child.x.endswith('%'):
                        child_x = parse_size_value(child.x, available_width)
                    else:
                        child_x = child.x
                
                if child.y is not None:
                    if isinstance(child.y, str) and child.y.endswith('%'):
                        child_y = parse_size_value(child.y, available_height)
                    else:
                        child_y = child.y
                
                # Calculate the space needed for this child
                needed_width = child_x + child_width
                needed_height = child_y + child_height
                
                max_width = max(max_width, needed_width)
                max_height = max(max_height, needed_height)
            
            # Use specified dimensions or calculated size + padding
            final_width = resolved_width if resolved_width is not None else max_width + 2 * self.padding
            final_height = resolved_height if resolved_height is not None else max_height + 2 * self.padding
            
            self.computed_size = constraints.constrain(final_width, final_height)
        
        return self.computed_size
    
    def render(self, x: int, y: int, constraints: BoxConstraints) -> Image.Image:
        """Render stack with background and positioned children"""
        width, height = self.computed_size
        
        # Create stack background
        stack_image = Image.new("RGBA", (width, height), self.bg_color)
        
        # Available space for children (excluding padding)
        available_width = width - 2 * self.padding
        available_height = height - 2 * self.padding
        
        # Render each child with full available constraints
        child_constraints = BoxConstraints(0, available_width, 0, available_height)
        
        for child in self.children:
            child_image = child.render(0, 0, child_constraints)
            child_width, child_height = child_image.size
            
            # Calculate child position
            child_x = self.padding  # Default to padding offset
            child_y = self.padding
            
            if child.x is not None:
                if isinstance(child.x, str) and child.x.endswith('%'):
                    child_x = self.padding + parse_size_value(child.x, available_width)
                else:
                    child_x = self.padding + child.x
            
            if child.y is not None:
                if isinstance(child.y, str) and child.y.endswith('%'):
                    child_y = self.padding + parse_size_value(child.y, available_height)
                else:
                    child_y = self.padding + child.y
            
            # Handle clipping if overflow is set to "clip"
            if self.overflow == "clip":
                # Ensure child doesn't exceed stack bounds
                child_x = max(self.padding, min(child_x, width - self.padding))
                child_y = max(self.padding, min(child_y, height - self.padding))
                
                # Crop child image if it extends beyond bounds
                max_child_width = width - child_x
                max_child_height = height - child_y
                
                if child_width > max_child_width or child_height > max_child_height:
                    crop_width = min(child_width, max_child_width)
                    crop_height = min(child_height, max_child_height)
                    child_image = child_image.crop((0, 0, crop_width, crop_height))
            
            # Paste child into stack
            if child_image.mode == 'RGBA':
                stack_image.paste(child_image, (int(child_x), int(child_y)), child_image)
            else:
                stack_image.paste(child_image, (int(child_x), int(child_y)))
        
        return stack_image


class WidgetTreeParser:
    """Parser to convert JSON to widget tree"""
    
    @staticmethod
    def parse(data: Dict) -> Widget:
        """Parse JSON structure into widget tree"""
        return WidgetTreeParser._parse_node(data)
    
    @staticmethod
    def _parse_widget_properties(node: Dict) -> Dict:
        """Extract common widget properties from node"""
        props = {}
        if 'padding' in node:
            props['padding'] = node['padding']
        if 'bg_color' in node:
            props['bg_color'] = node['bg_color']
        if 'width' in node:
            props['width'] = node['width']
        if 'height' in node:
            props['height'] = node['height']
        if 'flex' in node:
            props['flex'] = node['flex']
        if 'x' in node:
            props['x'] = node['x']
        if 'y' in node:
            props['y'] = node['y']
        if 'overflow' in node:
            props['overflow'] = node['overflow']
        return props
    
    @staticmethod
    def _parse_node(node: Dict) -> Widget:
        """Recursively parse a node in the JSON structure"""
        
        print(f"Parsing node: {list(node.keys())}")  # Debug print
        
        # Extract common properties
        props = WidgetTreeParser._parse_widget_properties(node)
        
        # Handle canvas (leaf node)
        if 'canvas' in node:
            canvas_config = node['canvas']
            layers = node.get('layers', [])
            print(f"Creating Canvas: {canvas_config['width']}x{canvas_config['height']}, layers: {len(layers)}")
            return Canvas(canvas_config, layers, **props)
        
        # Handle child wrapper
        if 'child' in node:
            print("Parsing child wrapper")
            child_node = node['child'].copy()
            # Pass through properties to child
            for key, value in props.items():
                if key not in child_node:
                    child_node[key] = value
            return WidgetTreeParser._parse_node(child_node)
        
        # Handle container
        if 'container' in node:
            container_data = node['container']
            print(f"Creating Container")
            child = WidgetTreeParser._parse_node(container_data)
            return Container(child, **props)
        
        # Handle row
        if 'row' in node:
            row_data = node['row']
            children = []
            print(f"Creating Row with data keys: {list(row_data.keys())}")
            
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
                    if key not in ['children', 'padding', 'bg_color', 'width', 'height', 'flex', 'x', 'y', 'overflow']:
                        print(f"Parsing row child: {key}")
                        child_widget = WidgetTreeParser._parse_node({key: value})
                        children.append(child_widget)
            
            print(f"Row created with {len(children)} children")
            return Row(children, **props)
        
        # Handle column
        if 'column' in node:
            column_data = node['column']
            children = []
            print(f"Creating Column with data keys: {list(column_data.keys())}")
            
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
                    if key not in ['children', 'padding', 'bg_color', 'width', 'height', 'flex', 'x', 'y', 'overflow']:
                        print(f"Parsing column child: {key}")
                        child_widget = WidgetTreeParser._parse_node({key: value})
                        children.append(child_widget)
            
            print(f"Column created with {len(children)} children")
            return Column(children, **props)
        
        # Handle stack
        if 'stack' in node:
            stack_data = node['stack']
            children = []
            print(f"Creating Stack with data keys: {list(stack_data.keys())}")
            
            # Check if stack has explicit children array
            if 'children' in stack_data:
                print("Found children array in stack")
                for i, child_data in enumerate(stack_data['children']):
                    print(f"Parsing stack child {i}: {list(child_data.keys())}")
                    child_widget = WidgetTreeParser._parse_node(child_data)
                    children.append(child_widget)
            else:
                # Parse all children of the stack (old format)
                for key, value in stack_data.items():
                    if key not in ['children', 'padding', 'bg_color', 'width', 'height', 'flex', 'x', 'y', 'overflow']:
                        print(f"Parsing stack child: {key}")
                        child_widget = WidgetTreeParser._parse_node({key: value})
                        children.append(child_widget)
            
            print(f"Stack created with {len(children)} children")
            return Stack(children, **props)
        
        raise ValueError(f"Unknown node structure: {node}")


class WidgetTreeRenderer:
    """Main renderer for widget trees"""
    
    def __init__(self, root_width: int, root_height: int):
        self.root_width = root_width
        self.root_height = root_height
    
    def render_from_json(self, json_data: Dict, output_path: str = "widget_output.png"):
        """Render widget tree from JSON and save to file"""
        # Parse JSON to widget tree
        root_widget = WidgetTreeParser.parse(json_data)
        
        # Create root constraints
        root_constraints = BoxConstraints(
            self.root_width, self.root_width,
            self.root_height, self.root_height
        )
        
        # Calculate sizes (bottom-up with constraints)
        root_widget.calculate_size(root_constraints)
        
        # Render the tree (top-down with constraints)
        final_image = root_widget.render(0, 0, root_constraints)
        
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
    # Example with constraints and flexbox layout
    testing = {
  "container": {
    "width": 1920,
    "height": 1080,
    "column": {
      "children": [
        {
          "height": "33.33%",
          "canvas": {
            "width": 1920,
            "height": 360,
            "background": "#FF6B6B"
          },
          "layers": [
              {
                          "type": "text",
                          "text": "RANDOM TEXT",
                          "size": 180,
                          "color": "#0F1314",
                          "x": "0%",
                          "y": "0%",
                          "anchor": "center"
                        }
              
          ]
        },
        {
          "height": "33.33%",
          "canvas": {
            "width": 1920,
            "height": 360,
            "background": "#4ECDC4"
          },
          "layers": []
        },
        {
          "height": "33.34%",
          "row": {
            "children": [
              {
                "width": "25%",
                "canvas": {
                  "width": 480,
                  "height": 360,
                  "background": "#45B7D1"
                },
                "layers": [
                    {
                          "type": "text",
                          "text": "RANDOM TEXT",
                          "size": 180,
                          "color": "#0F1314",
                          "x": "0%",
                          "y": "0%",
                          "anchor": "center"
                        }
                ]
              },
              {
                "width": "25%",
                "canvas": {
                  "width": 480,
                  "height": 360,
                  "background": "#96CEB4"
                },
                "layers": []
              },
              {
                "width": "25%",
                "stack": {
                  "children": [
                    {
                      "canvas": {
                        "width": 480,
                        "height": 360,
                        "background": "#A7FFC7"
                      },
                      "layers": []
                    },
                    {
                      "canvas": {
                        "width": 480,
                        "height": 360,
                        "background": "#ffffff"
                      },
                      "layers": [
                        {
                          "type": "gradient",
                          "gradient_type": "radial",
                          "colors": ["#8D37C3", "#7674FF", "#5F1EDA"],
                          "stops": [0, 0.5, 1],
                          "x": "50%",
                          "y": "50%",
                          "width": "100%",
                          "height": "100%",
                          "opacity": 0.8
                        },
                        {
                          "type": "text",
                          "text": "RANDOM TEXT",
                          "size": 180,
                          "color": "#0F1314",
                          "x": "0%",
                          "y": "0%",
                          "anchor": "center"
                        }
                      ]
                    }
                  ]
                }
              },
              {
                "width": "25%",
                "canvas": {
                  "width": 480,
                  "height": 360,
                  "background": "#DDA0DD"
                },
                "layers": []
              }
            ]
          }
        }
      ]
    }
  }
}

    # Render different examples
    renderer = WidgetTreeRenderer(1920, 1080)
    
    print("Rendering flexbox example...")
    renderer.render_from_json(testing, "testing.png")
    print("\nAll examples rendered successfully!")
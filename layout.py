import re
from typing import Dict, Any, List, Optional, Union
import json

class LayoutParser:
    """Parse layout strings into JSON structure"""
    
    def __init__(self):
        self.canvas_counter = 1
    
    def parse(self, layout_string: str) -> Dict[str, Any]:
        """
        Parse a layout string into JSON structure
        
        Format: container(widthxheight)[layout_content]
        """
        self.canvas_counter = 1  # Reset counter for each parse
        
        # Remove all whitespace for easier parsing
        layout_string = re.sub(r'\s+', '', layout_string)
        
        # Parse the root container
        container_match = re.match(r'container\((\d+)x(\d+)\)\[(.*)\]$', layout_string)
        if not container_match:
            raise ValueError("Invalid layout string format. Expected: container(widthxheight)[...]")
        
        width = int(container_match.group(1))
        height = int(container_match.group(2))
        content = container_match.group(3)
        
        # Parse the content inside container
        child_layout = self._parse_layout_element(content)
        
        return {
            "container": {
                "width": width,
                "height": height,
                **child_layout
            }
        }
    
    def _parse_layout_element(self, content: str) -> Dict[str, Any]:
        """Parse a single layout element (column, row, stack, or placeholder)"""
        
        # Check for placeholder
        placeholder_match = re.match(r'placeholder\(([^)]*)\)$', content)
        if placeholder_match:
            size_spec = placeholder_match.group(1)
            result = {f"canvas_{self.canvas_counter}": "PLACEHOLDER"}
            self.canvas_counter += 1
            
            # Add size specification if provided
            if size_spec:
                # Could be percentage like "33.33%" or dimension like "500x300"
                if 'x' in size_spec:
                    # Dimension format
                    width, height = size_spec.split('x')
                    result["width"] = int(width)
                    result["height"] = int(height)
                elif size_spec.endswith('%'):
                    # Percentage format - context determines if it's width or height
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
                children = self._parse_children(children_content)
                
                result = {
                    layout_type: {
                        "children": children
                    }
                }
                
                # Add size specification if provided
                if size_spec:
                    if size_spec.endswith('%'):
                        # Determine if it's width or height based on context
                        result["size"] = size_spec
                
                return result
        
        raise ValueError(f"Could not parse layout element: {content}")
    
    def _parse_children(self, children_content: str) -> List[Dict[str, Any]]:
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
                    child_data = self._parse_layout_element(current_child.strip())
                    children.append(child_data)
                current_child = ""
                i += 1
                continue
            
            current_child += char
            i += 1
        
        # Add the last child
        if current_child.strip():
            child_data = self._parse_layout_element(current_child.strip())
            children.append(child_data)
        
        return children
    
    def _apply_size_context(self, layout_json: Dict[str, Any], parent_type: str = None) -> Dict[str, Any]:
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
                            # For stack or unknown context, could be either
                            new_node["width"] = value  # Default to width
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
    
    def parse_and_format(self, layout_string: str) -> Dict[str, Any]:
        """Parse layout string and apply proper size contexts"""
        raw_json = self.parse(layout_string)
        formatted_json = self._apply_size_context(raw_json)
        return formatted_json


# Test and example usage
def test_parser():
    parser = LayoutParser()
    
    # Test the example layout string
    layout_string = "container(1920x1080)[column[placeholder(33.33%), placeholder(33.33%), row(33.34%)[placeholder(25%), placeholder(25%), stack(25%)[placeholder(), placeholder()], placeholder(25%)]]]"
    
    try:
        result = parser.parse_and_format(layout_string)
        print("Parsed Layout JSON:")
        print(json.dumps(result, indent=2))
        
        # Count placeholders
        json_str = json.dumps(result)
        canvas_count = json_str.count('"canvas_')
        print(f"\nTotal canvases to be created: {canvas_count}")
        
    except Exception as e:
        print(f"Error parsing layout: {e}")

def test_simple_cases():
    parser = LayoutParser()
    
    test_cases = [
        # Simple cases
        "container(800x600)[placeholder()]",
        "container(800x600)[row[placeholder(50%), placeholder(50%)]]",
        "container(800x600)[column[placeholder(30%), placeholder(70%)]]",
        "container(800x600)[stack[placeholder(), placeholder()]]",
        
        # Nested case
        "container(1200x800)[row[placeholder(25%), column[placeholder(50%), placeholder(50%)], placeholder(25%)]]"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"Test Case {i}: {test_case}")
        print('='*50)
        
        try:
            result = parser.parse_and_format(test_case)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing main example:")
    test_parser()
    
    print("\n\nTesting simple cases:")
    test_simple_cases()
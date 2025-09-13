from wand.image import Image
from wand.drawing import Drawing
from wand.color import Color
import json
import os

class PosterGenerator:
    def __init__(self):
        self.fonts_dir = "fonts/"
        self.images_dir = "images/"
        
        os.makedirs(self.fonts_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs("output", exist_ok=True)
    
    def create_poster_from_json(self, json_data, output_filename="poster.png"):
        canvas_config = json_data.get('canvas', {})
        width = canvas_config.get('width', 1920)
        height = canvas_config.get('height', 1080)
        background = canvas_config.get('background', '#FFFFFF')
        
        with Image(width=width, height=height, background=Color(background)) as canvas:
            for layer in json_data.get('layers', []):
                layer_type = layer.get('type')
                
                if layer_type == 'image':
                    self._add_image_layer(canvas, layer)
                elif layer_type == 'text':
                    self._add_text_layer(canvas, layer)
                elif layer_type == 'color_overlay':
                    self._add_color_overlay(canvas, layer)
            
            canvas.save(filename=f"output/{output_filename}")
            print(f"Poster saved as output/{output_filename}")
    
    def _calculate_position(self, canvas, x, y, anchor='top-left', element_width=0, element_height=0):
        """Calculate actual pixel position from percentage and anchor"""
        canvas_width = canvas.width
        canvas_height = canvas.height
        
        if isinstance(x, str) and x.endswith('%'):
            actual_x = (float(x[:-1]) / 100) * canvas_width
        else:
            actual_x = float(x)
            
        if isinstance(y, str) and y.endswith('%'):
            actual_y = (float(y[:-1]) / 100) * canvas_height
        else:
            actual_y = float(y)
        
        if anchor in ['top-center', 'center', 'bottom-center']:
            actual_x -= element_width / 2
        elif anchor in ['top-right', 'center-right', 'bottom-right']:
            actual_x -= element_width
            
        if anchor in ['center-left', 'center', 'center-right']:
            actual_y -= element_height / 2
        elif anchor in ['bottom-left', 'bottom-center', 'bottom-right']:
            actual_y -= element_height
            
        return int(actual_x), int(actual_y)
    
    def _get_text_dimensions(self, text, font_family, font_size):
        """Estimate text dimensions for anchor calculations"""
        estimated_width = len(text) * font_size * 0.6
        estimated_height = font_size
        return estimated_width, estimated_height
    
    def _add_image_layer(self, canvas, layer):
        src = layer.get('src')
        x = layer.get('x', 0)
        y = layer.get('y', 0)
        width = layer.get('width')
        height = layer.get('height')
        opacity = layer.get('opacity', 1.0)
        anchor = layer.get('anchor', 'top-left')
        
        try:
            image_path = os.path.join(self.images_dir, src) if not os.path.isabs(src) else src
            with Image(filename=image_path) as img:
                if width and height:
                    if isinstance(width, str) and width.endswith('%'):
                        width = int((float(width[:-1]) / 100) * canvas.width)
                    if isinstance(height, str) and height.endswith('%'):
                        height = int((float(height[:-1]) / 100) * canvas.height)
                    
                    img.resize(int(width), int(height))
                
                actual_x, actual_y = self._calculate_position(canvas, x, y, anchor, img.width, img.height)
                
                if opacity < 1.0:
                    img.alpha_channel = True
                    img.evaluate(operator='multiply', value=opacity, channel='alpha')
                
                canvas.composite(img, actual_x, actual_y)
                
        except Exception as e:
            print(f"Error adding image layer {src}: {e}")
    
    def _add_color_overlay(self, canvas, layer):
        """Add a color overlay rectangle using Drawing API"""
        color = layer.get('color', '#000000')
        x = layer.get('x', 0)
        y = layer.get('y', 0)
        width = layer.get('width', 100)
        height = layer.get('height', 100)
        opacity = layer.get('opacity', 0.5)
        anchor = layer.get('anchor', 'top-left')
        
        if isinstance(width, str) and width.endswith('%'):
            width = int((float(width[:-1]) / 100) * canvas.width)
        if isinstance(height, str) and height.endswith('%'):
            height = int((float(height[:-1]) / 100) * canvas.height)
        
        actual_x, actual_y = self._calculate_position(canvas, x, y, anchor, width, height)
        
        with Drawing() as draw:
            draw.fill_color = Color(color)
            draw.fill_opacity = opacity
            
            draw.rectangle(actual_x, actual_y, actual_x + width, actual_y + height)
            draw(canvas)
    
    def _add_text_layer(self, canvas, layer):
        text = layer.get('text', '')
        font = layer.get('font', 'Arial')
        size = layer.get('size', 24)
        color = layer.get('color', '#000000')
        x = layer.get('x', 0)
        y = layer.get('y', 0)
        anchor = layer.get('anchor', 'top-left')
        weight = layer.get('weight', 'normal')
        stroke_color = layer.get('stroke_color', None)
        stroke_width = layer.get('stroke_width', 0)
        
        text_width, text_height = self._get_text_dimensions(text, font, size)
        
        actual_x, actual_y = self._calculate_position(canvas, x, y, anchor, text_width, text_height)
        
        with Drawing() as draw:
            font_path = os.path.join(self.fonts_dir, font)
            if os.path.exists(font_path):
                draw.font = font_path
            else:
                draw.font_family = font
            
            draw.font_size = size
            draw.fill_color = Color(color)
            
            if weight == 'bold':
                draw.font_weight = 700
            
            if stroke_color and stroke_width > 0:
                draw.stroke_color = Color(stroke_color)
                draw.stroke_width = stroke_width
            
            draw.text(actual_x, actual_y, text)
            draw(canvas)


if __name__ == "__main__":
    generator = PosterGenerator()
    
    test_poster = {
        "canvas": {
            "width": 1200,
            "height": 800,
            "background": "#2C3E50"
        },
        "layers": [
            {
                "type": "image",
                "src": "background.jpg",
                "x": "0%",
                "y": "0%",
                "width": "100%",
                "height": "100%",
                "opacity": 1.0,
                "anchor": "top-left"
            },
            {
                "type": "text",
                "text": "ADMRLS",
                "font": "Arial",
                "size": 120,
                "weight": "bold",
                "color": "#FFFFFF",
                "stroke_color": "#000000",
                "stroke_width": 3,
                "x": "50%",
                "y": "40%",
                "anchor": "center"
            },
            {
                "type": "text",
                "text": "EXPERIENCE THE FUTURE",
                "font": "Arial",
                "size": 36,
                "weight": "normal",
                "color": "#ECF0F1",
                "x": "50%",
                "y": "55%",
                "anchor": "center"
            },
            {
                "type": "image",
                "src": "layer_1.jpg",
                "x": "5%",
                "y": "5%",
                "width": "20%",
                "height": "15%",
                "opacity": 1.0,
                "anchor": "top-left"
            },
            {
                "type": "text",
                "text": "www.admrls.com",
                "font": "Arial",
                "size": 24,
                "color": "#BDC3C7",
                "x": "95%",
                "y": "95%",
                "anchor": "bottom-right"
            },
            {
                "type": "color_overlay",
                "color": "#3498DB",
                "x": "0%",
                "y": "70%",
                "width": "100%",
                "height": "30%",
                "opacity": 0.3,
                "anchor": "top-left"
            }
        ]
    }
    
    admrls_poster_percentage = {
        "canvas": {
            "width": 1200,
            "height": 800,
            "background": "#FFFFFF"
        },
        "layers": [
            {
                "type": "image",
                "src": "background.jpg",
                "x": "0%",
                "y": "0%",
                "width": "100%",
                "height": "100%",
                "opacity": 1.0,
                "anchor": "top-left"
            },
            {
                "type": "image",
                "src": "layer_1.jpg",
                "x": "75%",
                "y": "50%",
                "width": "50%",
                "height": "100%",
                "opacity": 1.0,
                "anchor": "center"
            },
            {
                "type": "color_overlay",
                "color": "#9370DB",
                "x": "0%",
                "y": "0%",
                "width": "100%",
                "height": "100%",
                "opacity": 0.6,
                "anchor": "top-left"
            },
            {
                "type": "text",
                "text": "ADMRLS",
                "font": "Arial",
                "size": 120,
                "weight": "bold",
                "color": "#FFFFFF",
                "stroke_color": "#000000",
                "stroke_width": 2,
                "x": "50%",
                "y": "50%",
                "anchor": "center"
            }
        ]
    }
    
    print("Creating test poster with percentage positioning...")
    generator.create_poster_from_json(test_poster, "test_percentage_poster.png")
    
    print("Creating ADMRLS poster with percentage positioning...")
    generator.create_poster_from_json(admrls_poster_percentage, "admrls_percentage_poster.png")
    
    print("Done! Check output folder for:")
    print("- test_percentage_poster.png")
    print("- admrls_percentage_poster.png")
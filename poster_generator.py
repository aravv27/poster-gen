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
                elif layer_type == 'shape':
                    self._add_shape_layer(canvas, layer)
                elif layer_type == 'gradient':
                    self._add_gradient_layer(canvas, layer)
            
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
    
    def _apply_image_filters(self, img, filters):
        """
        Applies a list of filters (from JSON) to a Wand Image object, in order.
        Each filter must be a dict with a 'type' key.
        """
        for f in (filters or []):
            t = f.get('type')
            if t == 'gaussian_blur':
                img.blur(radius=f.get('radius', 0), sigma=f.get('sigma', 1))
            elif t == 'motion_blur':
                img.motion_blur(radius=f.get('radius', 0), sigma=f.get('sigma', 1), angle=f.get('angle', 0))
            elif t == 'radial_blur':
                img.radial_blur(degree=f.get('degree', 8))
            elif t == 'edge':
                img.edge(radius=f.get('radius', 1))
            elif t == 'emboss':
                img.emboss(radius=f.get('radius', 1), sigma=f.get('sigma', 0.5))
            elif t == 'charcoal':
                img.charcoal(radius=f.get('radius', 1.5), sigma=f.get('sigma', 0.5))
            elif t == 'vignette':
                img.vignette(
                        radius=f.get('radius', 12),
                        sigma=f.get('sigma', 10),
                        x=f.get('x', 20),
                        y=f.get('y', 20)
                    )
            elif t == 'sepia_tone':
                img.sepia_tone(threshold=f.get('threshold', 0.8))
            elif t == 'polaroid':
                # 'img.polaroid' returns a new image, use with care
                angle = f.get('angle', 0)
                with img.polaroid(angle) as poly_img:
                    img.sequence.clear()
                    img.sequence.append(poly_img)
                    img.read(blob=poly_img.make_blob())
            elif t == 'charcoal':
                img.charcoal(radius=f.get('radius', 1.5), sigma=f.get('sigma', 0.5))
            elif t == 'grayscale' or t == 'blackwhite':
                img.type = 'grayscale'
            elif t == 'brightness_contrast':
                img.brightness_contrast(
                    brightness=f.get('brightness', 0),
                    contrast=f.get('contrast', 0))
            elif t == 'modulate':
                img.modulate(
                    brightness=f.get('brightness', 100),
                    saturation=f.get('saturation', 100),
                    hue=f.get('hue', 100))
            elif t == 'gamma':
                img.gamma(f.get('gamma', 1.0))
            elif t == 'level':
                img.level(black=f.get('black', 0), white=f.get('white', 1.0), gamma=f.get('gamma', 1.0))
            elif t == 'distort':
                # Perspective, Barrel, Arc, etc.
                method = f.get('method', 'perspective')
                args = f.get('args', [])
                img.distort(method, args)
            elif t == 'implode':
                img.implode(amount=f.get('amount', 0.5))
            elif t == 'flip':
                img.flip()
            elif t == 'flop':
                img.flop()
            elif t == 'roll':
                img.roll(f.get('x_offset', 0), f.get('y_offset', 0))
            # ... add more as needed
            # Failsafe: muting unknown filter types
        return img

    
    def _add_image_layer(self, canvas, layer):
        print("Image layer called")
        src = layer.get('src')
        x = layer.get('x', 0)
        y = layer.get('y', 0)
        width = layer.get('width')
        height = layer.get('height')
        opacity = layer.get('opacity', 1.0)
        anchor = layer.get('anchor', 'top-left')
        filters = layer.get('filters', None)
        
        try:
            image_path = os.path.join(self.images_dir, src) if not os.path.isabs(src) else src
            with Image(filename=image_path) as img:
                if width and height:
                    if isinstance(width, str) and width.endswith('%'):
                        width = int((float(width[:-1]) / 100) * canvas.width)
                    if isinstance(height, str) and height.endswith('%'):
                        height = int((float(height[:-1]) / 100) * canvas.height)
                    
                    img.resize(int(width), int(height))
                
                self._apply_image_filters(img, filters)
                print(f"applied filters {filters}")
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
    
    def _add_shape_layer(self, canvas, layer):
        """Add a shape layer (rectangle, circle, ellipse, polygon)"""
        shape_type = layer.get('shape', 'rectangle')
        color = layer.get('color', '#000000')
        x = layer.get('x', 0)
        y = layer.get('y', 0)
        width = layer.get('width', 100)
        height = layer.get('height', 100)
        opacity = layer.get('opacity', 1.0)
        anchor = layer.get('anchor', 'top-left')
        stroke_color = layer.get('stroke_color', None)
        stroke_width = layer.get('stroke_width', 0)
        
        # Handle percentage values
        if isinstance(width, str) and width.endswith('%'):
            width = int((float(width[:-1]) / 100) * canvas.width)
        if isinstance(height, str) and height.endswith('%'):
            height = int((float(height[:-1]) / 100) * canvas.height)
        
        actual_x, actual_y = self._calculate_position(canvas, x, y, anchor, width, height)
        
        with Drawing() as draw:
            draw.fill_color = Color(color)
            draw.fill_opacity = opacity
            
            if stroke_color and stroke_width > 0:
                draw.stroke_color = Color(stroke_color)
                draw.stroke_width = stroke_width
            else:
                draw.stroke_opacity = 0
            
            if shape_type == 'rectangle':
                draw.rectangle(actual_x, actual_y, actual_x + width, actual_y + height)
            
            elif shape_type == 'circle':
                # For circle, use the smaller dimension as diameter
                radius = min(width, height) // 2
                center_x = actual_x + width // 2
                center_y = actual_y + height // 2
                draw.circle((center_x, center_y), (center_x + radius, center_y))
            
            elif shape_type == 'ellipse':
                center_x = actual_x + width // 2
                center_y = actual_y + height // 2
                draw.ellipse((center_x, center_y), (center_x + width//2, center_y + height//2))
            
            elif shape_type == 'polygon':
                # For polygon, expect 'points' in layer config
                points = layer.get('points', [])
                if points:
                    # Convert percentage points to actual coordinates
                    actual_points = []
                    for point in points:
                        px, py = point
                        if isinstance(px, str) and px.endswith('%'):
                            px = (float(px[:-1]) / 100) * canvas.width
                        if isinstance(py, str) and py.endswith('%'):
                            py = (float(py[:-1]) / 100) * canvas.height
                        actual_points.append((int(px), int(py)))
                    draw.polygon(actual_points)
            
            draw(canvas)

    def _add_gradient_layer(self, canvas, layer):
        # Type and parameters
        gradient_type = layer.get('gradient_type', 'linear') # 'linear', 'radial', 'conic'
        angle = layer.get('angle', 0)
        stops = layer.get('stops')
        start_color = layer.get('start_color', '#000000')   # fallback
        end_color = layer.get('end_color', '#FFFFFF')
        x = layer.get('x', 0)
        y = layer.get('y', 0)
        width = layer.get('width', '100%')
        height = layer.get('height', '100%')
        opacity = layer.get('opacity', 1.0)
        anchor = layer.get('anchor', 'top-left')

        # Handle percentage values
        if isinstance(width, str) and width.endswith('%'):
            width = int((float(width[:-1]) / 100) * canvas.width)
        if isinstance(height, str) and height.endswith('%'):
            height = int((float(height[:-1]) / 100) * canvas.height)
        actual_x, actual_y = self._calculate_position(canvas, x, y, anchor, width, height)

        # Build Magick pseudo-format string
        if stops and len(stops) >= 2:
            first_color = stops[0]["color"]
            last_color = stops[-1]["color"]
        else:
            first_color = start_color
            last_color = end_color


        # Create gradient descriptor. For linear use pseudo-image, for multi-stop, build stops string
        if gradient_type == 'linear':
            gradient_desc = f'gradient:{first_color}-{last_color}'
        elif gradient_type == 'radial':
            # Magick's 'radial-gradient' for radial
             gradient_desc = f'radial-gradient:{first_color}-{last_color}'
        elif gradient_type == 'conic':
            # Magick's 'conic-gradient'
            gradient_desc = f'gradient:{first_color}-{last_color}'
        else:
            gradient_desc = f'gradient:{first_color}-{last_color}'

        # Wand's pseudo() creates gradient image
        with Image(width=int(width), height=int(height)) as gradient_img:
            gradient_img.pseudo(int(width), int(height), gradient_desc)
            
            # Opacity
            if opacity < 1.0:
                gradient_img.alpha_channel = 'activate'
                gradient_img.evaluate(operator='set', value=1.0, channel='alpha')
                gradient_img.evaluate(operator='multiply', value=opacity, channel='alpha')

            # Composite onto canvas
            canvas.composite(gradient_img, int(actual_x), int(actual_y))


    
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
        align = layer.get('align', 'left')
        box = layer.get('box')  # [left, top, width, height]
        line_height = layer.get('line_height', 1.0)
        letter_spacing = layer.get('letter_spacing', 0)
        transform = layer.get('transform', None)
        vertical = layer.get('vertical', False)

        # Text transform
        if transform == "uppercase":
            text = text.upper()
        elif transform == "lowercase":
            text = text.lower()
        elif transform == "capitalize":
            text = text.title()

        # Multi-line handling
        lines = text.split('\n')

        # Font file (fallback)
        font_path = os.path.join(self.fonts_dir, font)
        font_to_use = font_path if os.path.exists(font_path) else font

        with Drawing() as draw:
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

            draw.text_alignment = align

            # Boxed, auto-wrapped multiline support
            if box:
                box_left, box_top, box_w, box_h = box
                y_cursor = int(box_top)
                for paragraph in text.split('\n'):
                    words = paragraph.split(' ')
                    line = ''
                    while words:
                        # Estimate line width
                        test_line = line + ('' if not line else ' ') + words[0]
                        text_metrics = draw.get_font_metrics(canvas, test_line, False)
                        if text_metrics.text_width > box_w and line:
                            # Draw current line, move down
                            draw.text(int(box_left), int(y_cursor + size), line)
                            y_cursor += size * line_height
                            line = words.pop(0)
                        else:
                            line = test_line
                            words.pop(0)
                    if line:
                        draw.text(int(box_left),int( y_cursor + size), line)
                        y_cursor += size * line_height
            else:
                # Each line, manually align as needed
                actual_x, actual_y = self._calculate_position(canvas, x, y, anchor, 0, 0)
                for idx, line in enumerate(lines):
                    # Letter spacing: Draw each glyph if specified
                    if letter_spacing:
                        draw_text_with_spacing(draw, line, font_to_use, size, 
                                            actual_x, actual_y + idx * size * line_height,
                                            letter_spacing, color)
                    else:
                        draw.text(int(actual_x), int(actual_y + idx * size * line_height), line)

            draw(canvas)

def draw_text_with_spacing(draw, text, font, font_size, x, y, spacing, color):
    """Draw text one character at a time with custom letter spacing."""
    # You need to import PIL or use Wand font metrics for accurate advance width.
    cursor_x = x
    for char in text:
        draw.text(int(cursor_x), int(y), char)
        # Use an approximate width for now, optionally refine with get_font_metrics
        cursor_x += font_size * 0.6 + spacing



if __name__ == "__main__":
    generator = PosterGenerator()
    admrls = {
  "canvas": {
    "width": 1920,
    "height": 1080,
    "background": "#2525DA"
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
      "anchor": "top-left",
      "filters": [
        {
          "type": "implode",
          "amount": 0.2
        }
      ]
    },
    {
      "type": "text",
      "text": "ENTERPRISE-LEVEL POSTER\nGENERATOR DEMO\nSupports multiline, alignment, and wraps long phrases automatically.",
      "font": "Arial",
      "size": 60,
      "color": "#F80505",
      "align": "center",
      "box": [480, 340, 960, 400],
      "line_height": 1.25,
      "letter_spacing": 3,
      "transform": "uppercase",
      "anchor": "top-left"
    },
    {
  "type": "gradient",
  "gradient_type": "radial",
  "start_color": "#CB2B2B",
  "end_color": "#2525DA",
  "x": "0%",
  "y": "0%",
  "width": "100%",
  "height": "100%",
  "opacity": .5,
  "anchor": "top-left"
}

  ]
}


    
    print("Creating ADMRLS poster with percentage positioning...")
    generator.create_poster_from_json(admrls, "filter_testing_text.png")
    print("Done! Check output folder for:")
    print("- admrls_percentage_poster.png")

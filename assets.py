from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from utils import hex_to_rgba, percent, get_anchor_pos
import os


def draw_image_layer(base, layer, width, height):
    print("image layer called")
    from PIL import ImageEnhance, ImageFilter
    import os

    src = layer.get('src')
    if not src or not os.path.exists(src):
        print(f"Image file not found: {src}")
        return
        
    x = percent(layer.get('x', 0), width)
    y = percent(layer.get('y', 0), height)
    anchor = layer.get('anchor', 'top-left')
    resize_w = layer.get('width', None)
    resize_h = layer.get('height', None)
    opacity = float(layer.get('opacity', 1.0))
    angle = layer.get('angle', 0)
    flip = bool(layer.get('flip', False))
    flop = bool(layer.get('flop', False))
    filters = layer.get('filters', [])

    try:
        img = Image.open(src).convert("RGBA")
        print(f"Loaded image: {src}, size: {img.size}")
    except Exception as e:
        print(f"Error loading image {src}: {e}")
        return

    # Resize (support percent/string)
    if resize_w and resize_h:
        new_w = percent(resize_w, width)
        new_h = percent(resize_h, height)
        img = img.resize((new_w, new_h), resample=Image.LANCZOS)
        print(f"Resized to: {new_w}x{new_h}")

    # Flip/flop/rotate
    if flip:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    if flop:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if angle:
        img = img.rotate(angle, expand=1)

    # Filters
    for f in filters:
        t = f.get('type')
        if t == "gaussian_blur":
            img = img.filter(ImageFilter.GaussianBlur(f.get('radius', 5)))
        elif t == "grayscale":
            # Better grayscale conversion
            gray = img.convert('L')
            img = Image.merge('LA', (gray, img.getchannel('A')))
            img = img.convert('RGBA')
        elif t == "brightness_contrast":
            factor = f.get('brightness', 1.0)
            img = ImageEnhance.Brightness(img).enhance(factor)
            factor = f.get('contrast', 1.0)
            img = ImageEnhance.Contrast(img).enhance(factor)

    # Opacity
    if opacity < 1.0:
        alpha = img.getchannel('A')
        alpha = alpha.point(lambda p: int(p * opacity))
        img.putalpha(alpha)

    # Anchor positioning - Fix the logic
    img_w, img_h = img.size
    if anchor == 'top-left':
        offset_x, offset_y = 0, 0
    elif anchor == 'center':
        offset_x = (width - img_w) // 2
        offset_y = (height - img_h) // 2
    elif anchor == 'top-center':
        offset_x = (width - img_w) // 2
        offset_y = 0
    elif anchor == 'center-left':
        offset_x = 0
        offset_y = (height - img_h) // 2
    elif anchor == 'center-right':
        offset_x = width - img_w
        offset_y = (height - img_h) // 2
    elif anchor == 'bottom-left':
        offset_x = 0
        offset_y = height - img_h
    elif anchor == 'bottom-center':
        offset_x = (width - img_w) // 2
        offset_y = height - img_h
    elif anchor == 'bottom-right':
        offset_x = width - img_w
        offset_y = height - img_h
    else:
        offset_x, offset_y = 0, 0
    
    final_x = int(offset_x + x)
    final_y = int(offset_y + y)
    
    # Debug positioning
    print(f"Image positioning: anchor={anchor}, final_pos=({final_x}, {final_y}), img_size={img.size}")
    
    # Ensure position is within canvas bounds
    if final_x < -img_w or final_y < -img_h or final_x > width or final_y > height:
        print(f"Warning: Image positioned outside canvas bounds")
    
    base.alpha_composite(img, (final_x, final_y))

def draw_text_layer(base, layer, width, height):
    print("text layer called")
    from PIL import ImageFont
    import os

    text = layer.get('text', '')
    print(f"Drawing text: '{text}'")
    
    if not text:
        print("No text provided")
        return
        
    font_path = layer.get('font', None)
    size = int(layer.get('size', 32))
    color = hex_to_rgba(layer.get('color', '#ffffff'))
    x = percent(layer.get('x', 0), width)
    y = percent(layer.get('y', 0), height)
    anchor = layer.get('anchor', 'top-left')
    align = layer.get('align', 'left')
    opacity = float(layer.get('opacity', 1.0))
    weight = layer.get('weight', 'normal')
    stroke_color = hex_to_rgba(layer.get('stroke_color', '#000000')) if 'stroke_color' in layer else None
    stroke_width = int(layer.get('stroke_width', 0))
    line_height = float(layer.get('line_height', 1.0))
    letter_spacing = int(layer.get('letter_spacing', 0))
    transform = layer.get('transform', None)
    shadow = layer.get('shadow', None)

    # Text transform
    if transform == "uppercase":
        text = text.upper()
    elif transform == "lowercase":
        text = text.lower()
    elif transform == "capitalize":
        text = text.title()

    # Font loading with better fallback
    font = None
    if font_path and os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, size)
            print(f"Loaded font: {font_path}")
        except Exception as e:
            print(f"Error loading font {font_path}: {e}")
    
    if font is None:
        try:
            # Try to load a system default font
            font = ImageFont.load_default()
            print("Using default font")
        except:
            # Create a minimal font fallback
            print("Using PIL default font")
            font = ImageFont.load_default()

    # Create text overlay
    txt_overlay = Image.new("RGBA", base.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt_overlay)
    lines = text.split('\n')

    # Calculate text dimensions for proper anchoring
    total_height = len(lines) * size * line_height
    max_width = max(draw.textlength(line, font=font) for line in lines) if lines else 0

    # Calculate anchor position using existing function
    draw_x, draw_y = get_anchor_pos(anchor, width, height, int(max_width), int(total_height))

    draw_x += x
    draw_y += y

    print(f"Text positioning: anchor={anchor}, pos=({draw_x}, {draw_y}), size={size}")

    # Draw each line
    for idx, line in enumerate(lines):
        if not line:  # Skip empty lines
            continue
            
        ly = int(draw_y + idx * size * line_height)
        lx = int(draw_x)
        
        # Shadow
        if shadow:
            sx = shadow.get('offset_x', 2)
            sy = shadow.get('offset_y', 2)
            scolor = hex_to_rgba(shadow.get('color', '#000000'))
            shadow_opacity = shadow.get('opacity', 0.5)
            scolor = (*scolor[:3], int(255 * shadow_opacity))
            draw.text((lx + sx, ly + sy), line, font=font, fill=scolor)
        
        # Main text
        if letter_spacing > 0:
            # Manual letter spacing
            cx = lx
            for ch in line:
                draw.text((cx, ly), ch, font=font, fill=color, 
                         stroke_fill=stroke_color, stroke_width=stroke_width)
                try:
                    ch_w = draw.textlength(ch, font=font)
                except:
                    ch_w = draw.textsize(ch, font=font)[0]  # Fallback for older PIL
                cx += ch_w + letter_spacing
        else:
            # Normal text drawing
            draw.text((lx, ly), line, font=font, fill=color, 
                     stroke_fill=stroke_color, stroke_width=stroke_width)

    # Apply opacity
    if opacity < 1.0:
        alpha = txt_overlay.getchannel('A')
        alpha = alpha.point(lambda p: int(p * opacity))
        txt_overlay.putalpha(alpha)

    base.alpha_composite(txt_overlay)
    print("Text layer completed")

def draw_ellipse(base, layer, width, height):
    color = hex_to_rgba(layer['color'])
    ele_w = percent(layer.get('width', 100), width)
    ele_h = percent(layer.get('height', 100), height)
    opacity = int(255 * layer.get('opacity', 1.0))
    blur = layer.get('blur', 0)
    anchor = layer.get('anchor', 'top-left')
    x = percent(layer.get('x', 0), width)
    y = percent(layer.get('y', 0), height)
    ellipse_img = Image.new("RGBA", (ele_w, ele_h), (0,0,0,0))
    draw = ImageDraw.Draw(ellipse_img)
    draw.ellipse([0,0,ele_w,ele_h], fill=(*color[:3], opacity))
    if blur > 0:
        ellipse_img = ellipse_img.filter(ImageFilter.GaussianBlur(blur))
    offset_x, offset_y = get_anchor_pos(anchor, width, height, ele_w, ele_h)
    base.alpha_composite(ellipse_img, (int(offset_x + x), int(offset_y + y)))

def draw_polygon(base, layer, width, height):
    color = hex_to_rgba(layer['color'])
    points = layer['points']
    # Find bounding box
    pxs = [percent(x, width) for x, _ in points]
    pys = [percent(y, height) for _, y in points]
    min_x, max_x = min(pxs), max(pxs)
    min_y, max_y = min(pys), max(pys)
    w, h = max_x - min_x, max_y - min_y
    opacity = int(255 * layer.get('opacity', 1.0))
    blur = layer.get('blur', 0)
    poly_img = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(poly_img)
    norm_pts = [(x - min_x, y - min_y) for x, y in zip(pxs, pys)]
    draw.polygon(norm_pts, fill=(*color[:3], opacity))
    if blur > 0:
        poly_img = poly_img.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(poly_img, (int(min_x), int(min_y)))
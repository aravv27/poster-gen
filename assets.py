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

# def draw_text_layer(base, layer, width, height):
#     print("text layer called")
#     from PIL import ImageFont
#     import os

#     text = layer.get('text', '')
#     print(f"Drawing text: '{text}'")
    
#     if not text:
#         print("No text provided")
#         return
        
#     font_path = layer.get('font', None)
#     size = int(layer.get('size', 32))
#     color = hex_to_rgba(layer.get('color', '#ffffff'))
#     x = percent(layer.get('x', 0), width)
#     y = percent(layer.get('y', 0), height)
#     anchor = layer.get('anchor', 'top-left')
#     align = layer.get('align', 'left')
#     opacity = float(layer.get('opacity', 1.0))
#     weight = layer.get('weight', 'normal')
#     stroke_color = hex_to_rgba(layer.get('stroke_color', '#000000')) if 'stroke_color' in layer else None
#     stroke_width = int(layer.get('stroke_width', 0))
#     line_height = float(layer.get('line_height', 1.0))
#     letter_spacing = int(layer.get('letter_spacing', 0))
#     transform = layer.get('transform', None)
#     shadow = layer.get('shadow', None)

#     # Text transform
#     if transform == "uppercase":
#         text = text.upper()
#     elif transform == "lowercase":
#         text = text.lower()
#     elif transform == "capitalize":
#         text = text.title()

#     # Font loading with better fallback
#     font = None
#     if font_path and os.path.exists(font_path):
#         try:
#             font = ImageFont.truetype(font_path, size)
#             print(f"Loaded font: {font_path}")
#         except Exception as e:
#             print(f"Error loading font {font_path}: {e}")
    
#     if font is None:
#         try:
#             # Try to load a system default font
#             font = ImageFont.load_default()
#             print("Using default font")
#         except:
#             # Create a minimal font fallback
#             print("Using PIL default font")
#             font = ImageFont.load_default()

#     # Create text overlay
#     txt_overlay = Image.new("RGBA", base.size, (0,0,0,0))
#     draw = ImageDraw.Draw(txt_overlay)
#     lines = text.split('\n')

#     # Calculate text dimensions for proper anchoring
#     total_height = len(lines) * size * line_height
#     max_width = max(draw.textlength(line, font=font) for line in lines) if lines else 0

#     # Calculate anchor position using existing function
#     draw_x, draw_y = get_anchor_pos(anchor, width, height, int(max_width), int(total_height))

#     draw_x += x
#     draw_y += y

#     print(f"Text positioning: anchor={anchor}, pos=({draw_x}, {draw_y}), size={size}")

#     # Draw each line
#     for idx, line in enumerate(lines):
#         if not line:  # Skip empty lines
#             continue
            
#         ly = int(draw_y + idx * size * line_height)
#         lx = int(draw_x)
        
#         # Shadow
#         if shadow:
#             sx = shadow.get('offset_x', 2)
#             sy = shadow.get('offset_y', 2)
#             scolor = hex_to_rgba(shadow.get('color', '#000000'))
#             shadow_opacity = shadow.get('opacity', 0.5)
#             scolor = (*scolor[:3], int(255 * shadow_opacity))
#             draw.text((lx + sx, ly + sy), line, font=font, fill=scolor)
        
#         # Main text
#         if letter_spacing > 0:
#             # Manual letter spacing
#             cx = lx
#             for ch in line:
#                 draw.text((cx, ly), ch, font=font, fill=color, 
#                          stroke_fill=stroke_color, stroke_width=stroke_width)
#                 try:
#                     ch_w = draw.textlength(ch, font=font)
#                 except:
#                     ch_w = draw.textsize(ch, font=font)[0]  # Fallback for older PIL
#                 cx += ch_w + letter_spacing
#         else:
#             # Normal text drawing
#             draw.text((lx, ly), line, font=font, fill=color, 
#                      stroke_fill=stroke_color, stroke_width=stroke_width)

#     # Apply opacity
#     if opacity < 1.0:
#         alpha = txt_overlay.getchannel('A')
#         alpha = alpha.point(lambda p: int(p * opacity))
#         txt_overlay.putalpha(alpha)

#     base.alpha_composite(txt_overlay)
#     print("Text layer completed")
def draw_text_layer(base, layer, width, height):
    """
    Renders a text layer on the given PIL Image (base), auto-fitting the font size
    so the text always fits within (width, height) of its canvas region.
    Includes fail-safes for font metrics quirks and robust anchor clamping.
    """
    from PIL import ImageFont, ImageDraw
    import os

    text = layer.get('text', '')
    if not text:
        print("No text provided")
        return
    
    font_path = layer.get('font')
    requested_size = int(layer.get('size', 32))
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

    # Split lines and strip whitespace
    lines = [line.strip() for line in text.split('\n')]

    # Fit-text logic: find max font size that fits
    min_font_size = 8
    fit_font_size = requested_size
    fit_font = None
    text_block_w, text_block_h = None, None

    dummy_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_dummy = ImageDraw.Draw(dummy_img)
    
    while fit_font_size >= min_font_size:
        # Font load logic
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, fit_font_size)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        line_widths = []
        line_heights = []
        max_line_width = 0
        total_text_height = 0

        for line in lines:
            try:
                bbox = draw_dummy.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            except Exception:
                w, h = draw_dummy.textsize(line, font=font)
            line_widths.append(w)
            line_heights.append(h)
            max_line_width = max(max_line_width, w)
            total_text_height += h

        total_text_height += int(len(lines) - 1) * int(fit_font_size * line_height - fit_font_size)
        spaced_line_widths = [lw + (len(line)-1)*letter_spacing for lw, line in zip(line_widths, lines)]
        max_spaced_line_width = max(spaced_line_widths)

        fits = (max_spaced_line_width <= width) and (total_text_height <= height)
        if fits:
            fit_font = font
            text_block_w = max_spaced_line_width
            text_block_h = total_text_height
            break
        fit_font_size -= 1

    if fit_font is None:
        fit_font = ImageFont.load_default()
        min_font_size = int(layer.get("size", 32))
        text_block_w = min_font_size * len(text) * 0.6
        text_block_h = min_font_size * line_height * len(lines)

    # --- ENTERPRISE FAIL-SAFES ---
    # If font metrics are buggy and measured box is too small, force size
    min_text_w = int(fit_font_size * len(text) * 0.6)
    min_text_h = int(fit_font_size * line_height * len(lines))
    if text_block_h < fit_font_size * 0.5:
        print("WARN: Measured text box is much smaller than font size, forcing height to estimated.")
        text_block_h = min_text_h
    if text_block_w < fit_font_size * 0.5:
        print("WARN: Measured text box is much smaller than font size, forcing width to estimated.")
        text_block_w = min_text_w

    # Clamp anchor position so block stays on canvas
    draw_x, draw_y = get_anchor_pos(anchor, width, height, int(text_block_w), int(text_block_h))

    draw_x += x
    draw_y += y
    draw_x = max(0, min(draw_x, width - text_block_w))
    draw_y = max(0, min(draw_y, height - text_block_h))

    # Create overlay for text drawing
    txt_overlay = Image.new("RGBA", (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(txt_overlay)
    cursor_y = draw_y

    # Actual drawing
    for idx, line in enumerate(lines):
        if letter_spacing > 0:
            cx = draw_x
            for ch in line:
                if shadow:
                    sx = shadow.get('offset_x', 2)
                    sy = shadow.get('offset_y', 2)
                    scolor = hex_to_rgba(shadow.get('color', '#000000'))
                    shadow_opacity = shadow.get('opacity', 0.5)
                    scolor = (*scolor[:3], int(255 * shadow_opacity))
                    draw.text((cx + sx, cursor_y + sy), ch, font=fit_font, fill=scolor)
                draw.text((cx, cursor_y), ch, font=fit_font, fill=color, 
                          stroke_fill=stroke_color, stroke_width=stroke_width)
                try:
                    ch_w = draw.textlength(ch, font=fit_font)
                except:
                    ch_w = draw.textsize(ch, font=fit_font)[0]
                cx += ch_w + letter_spacing
        else:
            if shadow:
                sx = shadow.get('offset_x', 2)
                sy = shadow.get('offset_y', 2)
                scolor = hex_to_rgba(shadow.get('color', '#000000'))
                shadow_opacity = shadow.get('opacity', 0.5)
                scolor = (*scolor[:3], int(255 * shadow_opacity))
                draw.text((draw_x + sx, cursor_y + sy), line, font=fit_font, fill=scolor)
            draw.text((draw_x, cursor_y), line, font=fit_font, fill=color, 
                      stroke_fill=stroke_color, stroke_width=stroke_width)
        try:
            lh = draw.textbbox((0, 0), line, font=fit_font)[3] - draw.textbbox((0, 0), line, font=fit_font)[1]
        except Exception:
            lh = fit_font_size
        cursor_y += int(lh * line_height)

    if opacity < 1.0:
        alpha = txt_overlay.getchannel('A')
        alpha = alpha.point(lambda p: int(p * opacity))
        txt_overlay.putalpha(alpha)

    base.alpha_composite(txt_overlay)
    print("Text layer completed: size {}, anchor {}, x {}, y {}".format(fit_font_size, anchor, draw_x, draw_y))
    print("Requested size:", requested_size)
    print("Final font size:", fit_font_size)
    print("Text block size (w,h):", text_block_w, text_block_h)
    print("Anchor position:", draw_x, draw_y)
    print("Drawing lines:", lines)
    print("Text color RGBA:", color)
    print("Opacity:", opacity)
    print("Font loaded:", fit_font)

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
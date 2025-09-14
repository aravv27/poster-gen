import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from utils import hex_to_rgba, percent, get_anchor_pos


def draw_radial_gradient(base, layer, width, height):
    # Support both old format (start_color, end_color) and new format (colors array)
    if 'colors' in layer:
        colors = [hex_to_rgba(color) for color in layer['colors']]
        # Optional: custom stop positions (default: evenly spaced)
        stops = layer.get('stops', None)
        if stops is None:
            stops = np.linspace(0, 1, len(colors))
    else:
        # Backward compatibility with old format
        colors = [hex_to_rgba(layer['start_color']), hex_to_rgba(layer['end_color'])]
        stops = [0, 1]
    
    center_x = percent(layer.get('x', '50%'), width)
    center_y = percent(layer.get('y', '50%'), height)
    grad_w = percent(layer.get('width', width), width)
    grad_h = percent(layer.get('height', height), height)
    opacity = layer.get('opacity', 1.0)
    anchor = layer.get('anchor', 'top-left')
    
    # Create gradient on the full canvas size to avoid rectangular artifacts
    y, x = np.ogrid[:height, :width]
    
    # Get the actual position where gradient center should be
    offset_x, offset_y = get_anchor_pos(anchor, width, height, grad_w, grad_h)
    actual_center_x = offset_x + center_x
    actual_center_y = offset_y + center_y
    
    # Calculate distance from center
    dx = x - actual_center_x
    dy = y - actual_center_y
    
    # Use the smaller dimension as radius for circular gradient
    max_radius = min(grad_w, grad_h) / 2
    distance = np.sqrt(dx**2 + dy**2)
    
    # Normalize distance (0 at center, 1 at max_radius)
    normalized_distance = np.clip(distance / max_radius, 0, 1)
    
    # Create the gradient array for full canvas
    grad_array = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Multi-color gradient blending
    for c in range(3):  # RGB channels
        # Initialize with first color
        color_values = np.full_like(normalized_distance, colors[0][c], dtype=float)
        
        # Blend between each color stop
        for i in range(len(colors) - 1):
            start_stop = stops[i]
            end_stop = stops[i + 1]
            start_color = colors[i][c]
            end_color = colors[i + 1][c]
            
            # Create mask for this segment
            segment_mask = (normalized_distance >= start_stop) & (normalized_distance <= end_stop)
            
            if np.any(segment_mask):
                # Calculate local blend factor within this segment
                segment_range = end_stop - start_stop
                if segment_range > 0:
                    local_blend = (normalized_distance - start_stop) / segment_range
                    local_blend = np.clip(local_blend, 0, 1)
                    blended_color = start_color * (1 - local_blend) + end_color * local_blend
                    color_values = np.where(segment_mask, blended_color, color_values)
        
        grad_array[..., c] = color_values.astype(np.uint8)
    
    # Create alpha mask - fully opaque at center, transparent at edges
    alpha_mask = (1 - normalized_distance) * opacity
    grad_array[..., 3] = (alpha_mask * 255).astype(np.uint8)
    
    # Only apply gradient within the specified bounds
    mask = (distance <= max_radius)
    grad_array[..., 3] = np.where(mask, grad_array[..., 3], 0)
    
    grad_img = Image.fromarray(grad_array, mode='RGBA')
    base.alpha_composite(grad_img, (0, 0))

def draw_linear_gradient(base, layer, width, height):
    colors = [hex_to_rgba(c) for c in layer.get('colors')]
    stops = layer.get('stops', np.linspace(0, 1, len(colors)))
    angle_deg = float(layer.get('angle', 0)) # 0: left-to-right, 90: top-to-bottom

    opacity = layer.get('opacity', 1.0)
    grad_w = percent(layer.get('width', width), width)
    grad_h = percent(layer.get('height', height), height)
    anchor = layer.get('anchor', 'top-left')

    # Angle in radians, origin at left border, angle 0 = horizontal
    theta = np.deg2rad(angle_deg)

    # Linear axis: compute start and end points based on anchor and angle
    offset_x, offset_y = get_anchor_pos(anchor, width, height, grad_w, grad_h)
    x0 = offset_x
    y0 = offset_y
    x1 = x0 + grad_w * np.cos(theta)
    y1 = y0 + grad_h * np.sin(theta)

    # Each pixel's projection onto the gradient vector
    y, x = np.ogrid[:height, :width]
    px = x - x0
    py = y - y0
    grad_vec = np.array([x1-x0, y1-y0])
    grad_vec_norm = np.linalg.norm(grad_vec)
    if grad_vec_norm == 0:
        grad_vec_norm = 1
    proj = (px * grad_vec[0] + py * grad_vec[1]) / grad_vec_norm**2
    normalized_pos = np.clip(proj, 0, 1)

    grad_array = np.zeros((height, width, 4), dtype=np.uint8)
    for c in range(3):
        color_values = np.full_like(normalized_pos, colors[0][c], dtype=float)
        for i in range(len(colors)-1):
            start_stop, end_stop = stops[i], stops[i+1]
            start_c, end_c = colors[i][c], colors[i+1][c]
            mask = (normalized_pos >= start_stop) & (normalized_pos <= end_stop)
            if np.any(mask):
                rng = end_stop - start_stop
                if rng > 0:
                    local_blend = (normalized_pos - start_stop) / rng
                    local_blend = np.clip(local_blend, 0, 1)
                    blended = start_c * (1 - local_blend) + end_c * local_blend
                    color_values = np.where(mask, blended, color_values)
        grad_array[..., c] = color_values.astype(np.uint8)
    grad_array[..., 3] = int((opacity * 255))
    grad_img = Image.fromarray(grad_array, mode='RGBA')
    base.alpha_composite(grad_img, (0,0))

# MESH GRADIENT: Multiple color anchors
def draw_mesh_gradient(base, layer, width, height):
    control_points = layer['mesh_points'] # List of {"x":..., "y":..., "color":...} dicts
    points = [(percent(pt["x"], width), percent(pt["y"], height)) for pt in control_points]
    colors = [hex_to_rgba(pt["color"]) for pt in control_points]
    opacity = layer.get('opacity', 1.0)
    grad_array = np.zeros((height, width, 4), dtype=np.uint8)
    y, x = np.ogrid[:height, :width]
    for c in range(3):
        # Inverse-distance weighted blending per channel
        weighted = np.zeros((height, width), dtype=float)
        total_w = np.zeros((height, width), dtype=float)

        for (px, py), color in zip(points, colors):
            dist = np.sqrt((x - px) ** 2 + (y - py) ** 2)
            # Avoid division by zero
            dist = np.maximum(dist, 1e-3)
            w = 1.0 / dist
            weighted += color[c] * w
            total_w += w
        grad_array[..., c] = (weighted / total_w).astype(np.uint8)
    grad_array[..., 3] = int((opacity * 255))
    grad_img = Image.fromarray(grad_array, mode='RGBA')
    base.alpha_composite(grad_img,(0,0))

# SHAPE BLUR GRADIENT: Gradient with blur in custom mask (ellipse/circle/rect)
def draw_shape_blur_gradient(base, layer, width, height):
    # Draw the base gradient first (reuse one of the other functions, e.g., radial or linear)
    temp_img = Image.new('RGBA', (width, height), (0,0,0,0))
    temp_layer = layer.copy()
    temp_layer['opacity'] = 1.0  # blur works better before alpha adjustment
    if layer.get('shape_gradient_type', 'linear') == 'radial':
        draw_radial_gradient(temp_img, temp_layer, width, height)
    else:
        draw_linear_gradient(temp_img, temp_layer, width, height)
    # Create a mask for shape
    shape = layer.get('shape', 'ellipse') # "ellipse" or "rect"
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    shape_x = percent(layer.get('shape_x', '0%'), width)
    shape_y = percent(layer.get('shape_y', '0%'), height)
    shape_w = percent(layer.get('shape_width', '100%'), width)
    shape_h = percent(layer.get('shape_height', '100%'), height)
    rect = (shape_x, shape_y, shape_x + shape_w, shape_y + shape_h)
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    if shape == 'ellipse':
        draw.ellipse(rect, fill=255)
    else:
        draw.rectangle(rect, fill=255)
    # Apply mask and blur
    blurred = temp_img.filter(ImageFilter.GaussianBlur(radius=layer.get('blur_radius', 20)))
    gradient_masked = Image.composite(blurred, Image.new('RGBA', (width,height)), mask)
    gradient_masked.putalpha(int(layer.get('opacity', 1.0) * 255))
    base.alpha_composite(gradient_masked, (0,0))

def draw_color_overlay(base, layer, width, height):
    color = hex_to_rgba(layer['color'])
    overlay_w = percent(layer.get('width', width), width)
    overlay_h = percent(layer.get('height', height), height)
    x = percent(layer.get('x', 0), width)
    y = percent(layer.get('y', 0), height)
    anchor = layer.get('anchor', 'top-left')
    opacity = int(255 * layer.get('opacity', 1.0))
    blur = layer.get('blur', 0)
    overlay = Image.new("RGBA", (overlay_w, overlay_h), (*color[:3], opacity))
    if blur > 0:
        overlay = overlay.filter(ImageFilter.GaussianBlur(blur))
    offset_x, offset_y = get_anchor_pos(anchor, width, height, overlay_w, overlay_h)
    base.alpha_composite(overlay, (int(offset_x + x), int(offset_y + y)))

def draw_spray_noise(base, layer, width, height):
    # "center_x", "center_y", "radius_x", "radius_y" in px or percent, "strength", "opacity"
    center_x = percent(layer.get('center_x', '70%'), width)
    center_y = percent(layer.get('center_y', '20%'), height)
    rx = percent(layer.get('radius_x', '30%'), width)
    ry = percent(layer.get('radius_y', '15%'), height)
    color1 = hex_to_rgba(layer.get('color1', "#44defb"))
    color2 = hex_to_rgba(layer.get('color2', "#d97bfd"))
    opacity = float(layer.get('opacity', 0.2))
    noise_scale = layer.get('noise_scale', 1.6)  # higher = finer dots
    strength = layer.get('strength', 0.7)  # lower = more holes

    yy, xx = np.ogrid[:height, :width]
    ellipse_mask = (((xx-center_x)/rx)**2 + ((yy-center_y)/ry)**2) <= 1.0
    # make "powder" effect:
    noise = np.random.rand(height, width)
    noise = (noise + 0.5 * np.random.rand(height, width) / noise_scale)
    mask = (noise > strength) & ellipse_mask
    out_arr = np.zeros((height, width, 4), dtype=np.uint8)
    # Blend uniformly between color1 and color2 in ellipse region
    blend_map = np.linspace(0, 1, width)[None, :]  # H x W
    for c in range(3):
        out_arr[..., c] = (color1[c] * (1-blend_map) + color2[c] * blend_map).astype(np.uint8)
    out_arr[..., 3] = np.where(mask, int(255 * opacity), 0)

    img = Image.fromarray(out_arr, mode="RGBA")
    base.alpha_composite(img, (0, 0))
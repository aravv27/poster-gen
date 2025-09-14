import json
from PIL import Image
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


def generate_cosmic_poster(config):
    width = config['canvas']['width']
    height = config['canvas']['height']
    background = config['canvas'].get('background', '#000000')
    base = Image.new("RGBA", (width, height), hex_to_rgba(background))
    for layer in config['layers']:
        draw_layer(base, layer, width, height)
    base.convert('RGB').save('gradient.jpg', quality=95)
    print("Saved as gradient.jpg")

if __name__ == "__main__":
    with open('admrls_poster.json') as f:
        config = json.load(f)
    generate_cosmic_poster(config)
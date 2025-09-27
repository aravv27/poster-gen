class Tool_config:
    generate_layout = {
    "name": "generate_layout",
    "description": "Generate a structured layout JSON from a string description. Creates hierarchical layouts with containers, rows, columns, stacks, and placeholders for UI design and canvas placement.",
    "parameters": {
        "type": "object",
        "properties": {
        "layout_string": {
            "type": "string",
            "description": "String describing the layout structure using the format: container(widthxheight)[layout_content]. Supports nested row, column, stack containers and placeholder elements with size specifications."
        }
        },
        "required": ["layout_string"]
    }
    }

    canvas_tool = {
            "name": "generate_canvas",
            "description": "Generate canvas configuration with specified dimensions and background color",
            "parameters": {
                "type": "object",
                "properties": {
                    "width": {
                        "type": "integer",
                        "description": "Canvas width in pixels (must be positive)"
                    },
                    "height": {
                        "type": "integer", 
                        "description": "Canvas height in pixels (must be positive)"
                    },
                    "background": {
                        "type": "string",
                        "description": "Background color as hex string (default: #000000)"
                    }
                },
                "required": ["width", "height"]
            }
        }

    radial_gradient_tool = {
            "name": "generate_radial_gradient",
            "description": "Generate a radial gradient configuration with colors radiating from a center point",
            "parameters": {
                "type": "object",
                "properties": {
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of color strings (hex, rgb, or named colors)"
                    },
                    "stops": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Optional list of stop positions (0.0 to 1.0) for color transitions"
                    },
                    "start_color": {
                        "type": "string",
                        "description": "Start color (alternative to colors array)"
                    },
                    "end_color": {
                        "type": "string",
                        "description": "End color (alternative to colors array)"
                    },
                    "x": {
                        "type": "string",
                        "description": "X coordinate of gradient center (pixels as integer or percentage as string, default: '50%')"
                    },
                    "y": {
                        "type": "string",
                        "description": "Y coordinate of gradient center (pixels as integer or percentage as string, default: '50%')"
                    },
                    "width": {
                        "type": "string",
                        "description": "Width of gradient area (pixels as integer or percentage as string)"
                    },
                    "height": {
                        "type": "string",
                        "description": "Height of gradient area (pixels as integer or percentage as string)"
                    },
                    "opacity": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Opacity of the gradient (0.0 to 1.0, default: 1.0)"
                    },
                    "anchor": {
                        "type": "string",
                        "enum": ["top-left", "top-center", "top-right", "center-left", "center", "center-right", "bottom-left", "bottom-center", "bottom-right"],
                        "description": "Anchor position for gradient placement (default: 'top-left')"
                    }
                },
                "required": [],
                "anyOf": [
                    {"required": ["colors"]},
                    {"required": ["start_color", "end_color"]}
                ]
            }
        }

    linear_gradient_tool = {
            "name": "generate_linear_gradient",
            "description": "Generate a linear gradient configuration with colors transitioning in a straight line",
            "parameters": {
                "type": "object",
                "properties": {
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of color strings (hex, rgb, or named colors)",
                        "minItems": 2
                    },
                    "stops": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Optional list of stop positions (0.0 to 1.0) for color transitions"
                    },
                    "angle": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 360,
                        "description": "Angle of gradient direction in degrees (default: 0)"
                    },
                    "opacity": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Opacity of the gradient (0.0 to 1.0, default: 1.0)"
                    },
                    "width": {
                        "type": "string",
                        "description": "Width of gradient area (pixels as integer or percentage as string)"
                    },
                    "height": {
                        "type": "string",
                        "description": "Height of gradient area (pixels as integer or percentage as string)"
                    },
                    "anchor": {
                        "type": "string",
                        "enum": ["top-left", "top-center", "top-right", "center-left", "center", "center-right", "bottom-left", "bottom-center", "bottom-right"],
                        "description": "Anchor position for gradient placement (default: 'top-left')"
                    }
                },
                "required": ["colors"]
            }
        }

    mesh_gradient_tool = {
            "name": "generate_mesh_gradient",
            "description": "Generate a mesh gradient configuration with multiple color points creating smooth transitions",
            "parameters": {
                "type": "object",
                "properties": {
                    "mesh_points": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "string",
                                    "description": "X coordinate (pixels as integer or percentage as string)"
                                },
                                "y": {
                                    "type": "string",
                                    "description": "Y coordinate (pixels as integer or percentage as string)"
                                },
                                "color": {
                                    "type": "string",
                                    "description": "Color at this mesh point (hex, rgb, or named color)"
                                }
                            },
                            "required": ["x", "y", "color"]
                        },
                        "description": "Array of mesh points defining gradient colors and positions",
                        "minItems": 2
                    },
                    "opacity": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Opacity of the gradient (0.0 to 1.0, default: 1.0)"
                    }
                },
                "required": ["mesh_points"]
            }
        }

    shape_blur_gradient_tool = {
            "name": "generate_shape_blur_gradient",
            "description": "Generate a shape-based gradient with blur effects for smooth color transitions",
            "parameters": {
                "type": "object",
                "properties": {
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of color strings (hex, rgb, or named colors)",
                        "minItems": 2
                    },
                    "stops": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Optional list of stop positions (0.0 to 1.0) for color transitions"
                    },
                    "angle": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 360,
                        "description": "Angle for gradient direction in degrees"
                    },
                    "shape_gradient_type": {
                        "type": "string",
                        "enum": ["linear", "radial"],
                        "description": "Type of gradient within the shape (default: 'linear')"
                    },
                    "shape": {
                        "type": "string",
                        "enum": ["ellipse", "rectangle", "circle"],
                        "description": "Shape type for the gradient (default: 'ellipse')"
                    },
                    "shape_x": {
                        "type": "string",
                        "description": "Shape X position (pixels as integer or percentage as string, default: '0%')"
                    },
                    "shape_y": {
                        "type": "string",
                        "description": "Shape Y position (pixels as integer or percentage as string, default: '0%')"
                    },
                    "shape_width": {
                        "type": "string",
                        "description": "Shape width (pixels as integer or percentage as string, default: '100%')"
                    },
                    "shape_height": {
                        "type": "string",
                        "description": "Shape height (pixels as integer or percentage as string, default: '100%')"
                    },
                    "blur_radius": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Blur radius in pixels for smooth edges (default: 20)"
                    },
                    "opacity": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Opacity of the gradient (0.0 to 1.0, default: 1.0)"
                    }
                },
                "required": ["colors"]
            }
        }

    color_overlay_tool = {
        "name": "generate_color_overlay",
        "description": "Generate a solid color overlay configuration with positioning and effects",
        "parameters": {
            "type": "object",
            "properties": {
                "color": {
                    "type": "string",
                    "description": "Overlay color (hex, rgb, or named color)"
                },
                "width": {
                    "type": "string",
                    "description": "Width of overlay area (pixels as integer or percentage as string)"
                },
                "height": {
                    "type": "string",
                    "description": "Height of overlay area (pixels as integer or percentage as string)"
                },
                "x": {
                    "type": "string",
                    "description": "X coordinate for overlay position (pixels as integer or percentage as string, default: 0)"
                },
                "y": {
                    "type": "string",
                    "description": "Y coordinate for overlay position (pixels as integer or percentage as string, default: 0)"
                },
                "anchor": {
                    "type": "string",
                    "enum": ["top-left", "top-center", "top-right", "center-left", "center", "center-right", "bottom-left", "bottom-center", "bottom-right"],
                    "description": "Anchor position for overlay placement (default: 'top-left')"
                },
                "opacity": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Opacity of the overlay (0.0 to 1.0, default: 1.0)"
                },
                "blur": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Blur amount in pixels for soft edges (default: 0)"
                }
            },
            "required": ["color"]
        }
    }

    generate_image_layer = {
        "name": "generate_image_layer",
        "description": "Generate an image layer with positioning, transformations, and effects.",
        "parameters": {
            "type": "object",
            "properties": {
                "src": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "x": {
                    "type": "string",
                    "description": "X position (pixels as integer or percentage as string, default: 0)"
                },
                "y": {
                    "type": "string", 
                    "description": "Y position (pixels as integer or percentage as string, default: 0)"
                },
                "anchor": {
                    "type": "string",
                    "description": "Anchor point ('top-left', 'center', 'bottom-right', etc., default: 'top-left')"
                },
                "width": {
                    "type": "string",
                    "description": "Image width (pixels as integer or percentage as string)"
                },
                "height": {
                    "type": "string",
                    "description": "Image height (pixels as integer or percentage as string)"
                },
                "opacity": {
                    "type": "number",
                    "description": "Opacity (0.0 to 1.0, default: 1.0)"
                },
                "angle": {
                    "type": "number",
                    "description": "Rotation angle in degrees (default: 0)"
                },
                "flip": {
                    "type": "boolean",
                    "description": "Flip vertically (default: false)"
                },
                "flop": {
                    "type": "boolean",
                    "description": "Flip horizontally (default: false)"
                },
                "filters": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of filter objects: {type: 'gaussian_blur', radius: 5}, {type: 'grayscale'}, {type: 'brightness_contrast', brightness: 1.2, contrast: 1.1}"
                }
            },
            "required": ["src"]
        }
    }

    generate_text_layer = {
        "name": "generate_text_layer",
        "description": "Generate a text layer with typography, positioning, and styling options.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text content (use \\n for line breaks)"
                },
                "x": {
                    "type": "string",
                    "description": "X position (pixels as integer or percentage as string, default: 0)"
                },
                "y": {
                    "type": "string",
                    "description": "Y position (pixels as integer or percentage as string, default: 0)"
                },
                "anchor": {
                    "type": "string",
                    "description": "Anchor point ('top-left', 'center', 'bottom-right', etc., default: 'top-left')"
                },
                "font": {
                    "type": "string",
                    "description": "Path to font file"
                },
                "size": {
                    "type": "integer",
                    "description": "Font size in pixels (default: 32)"
                },
                "color": {
                    "type": "string",
                    "description": "Text color in hex format (default: #ffffff)"
                },
                "align": {
                    "type": "string",
                    "description": "Text alignment ('left', 'center', 'right', default: 'left')"
                },
                "opacity": {
                    "type": "number",
                    "description": "Opacity (0.0 to 1.0, default: 1.0)"
                },
                "weight": {
                    "type": "string",
                    "description": "Font weight ('normal', 'bold', default: 'normal')"
                },
                "stroke_color": {
                    "type": "string",
                    "description": "Stroke/outline color in hex format"
                },
                "stroke_width": {
                    "type": "integer",
                    "description": "Stroke width in pixels (default: 0)"
                },
                "line_height": {
                    "type": "number",
                    "description": "Line height multiplier (default: 1.0)"
                },
                "letter_spacing": {
                    "type": "integer",
                    "description": "Extra spacing between letters in pixels (default: 0)"
                },
                "transform": {
                    "type": "string",
                    "description": "Text transform ('uppercase', 'lowercase', 'capitalize')"
                },
                "shadow": {
                    "type": "object",
                    "description": "Shadow object with offset_x, offset_y, color, opacity properties"
                }
            },
            "required": ["text"]
        }
    }

    generate_ellipse = {
        "name": "generate_ellipse",
        "description": "Generate an ellipse shape layer.",
        "parameters": {
            "type": "object",
            "properties": {
                "color": {
                    "type": "string",
                    "description": "Fill color in hex format"
                },
                "x": {
                    "type": "string",
                    "description": "X position (pixels as integer or percentage as string, default: 0)"
                },
                "y": {
                    "type": "string",
                    "description": "Y position (pixels as integer or percentage as string, default: 0)"
                },
                "width": {
                    "type": "string",
                    "description": "Ellipse width (pixels as integer or percentage as string, default: 100)"
                },
                "height": {
                    "type": "string",
                    "description": "Ellipse height (pixels as integer or percentage as string, default: 100)"
                },
                "anchor": {
                    "type": "string",
                    "description": "Anchor point for positioning (default: 'top-left')"
                },
                "opacity": {
                    "type": "number",
                    "description": "Opacity (0.0 to 1.0, default: 1.0)"
                },
                "blur": {
                    "type": "integer",
                    "description": "Blur radius in pixels (default: 0)"
                }
            },
            "required": ["color"]
        }
    }

    generate_polygon = {
        "name": "generate_polygon",
        "description": "Generate a polygon shape layer.",
        "parameters": {
            "type": "object",
            "properties": {
                "color": {
                    "type": "string",
                    "description": "Fill color in hex format"
                },
                "points": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "description": "Array of [x, y] coordinate pairs as strings (pixels or percentages). Example: [['0', '0'], ['100', '0'], ['50', '100']]"
                },
                "opacity": {
                    "type": "number",
                    "description": "Opacity (0.0 to 1.0, default: 1.0)"
                },
                "blur": {
                    "type": "integer",
                    "description": "Blur radius in pixels (default: 0)"
                }
            },
            "required": ["color", "points"]
        }
    }
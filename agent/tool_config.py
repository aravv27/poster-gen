class Tool_config:
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
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "X coordinate of gradient center (pixels or percentage, default: '50%')"
                    },
                    "y": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Y coordinate of gradient center (pixels or percentage, default: '50%')"
                    },
                    "width": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Width of gradient area (pixels or percentage)"
                    },
                    "height": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Height of gradient area (pixels or percentage)"
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
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Width of gradient area (pixels or percentage)"
                    },
                    "height": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Height of gradient area (pixels or percentage)"
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
                                    "oneOf": [
                                        {"type": "integer"},
                                        {"type": "string"}
                                    ],
                                    "description": "X coordinate (pixels or percentage)"
                                },
                                "y": {
                                    "oneOf": [
                                        {"type": "integer"},
                                        {"type": "string"}
                                    ],
                                    "description": "Y coordinate (pixels or percentage)"
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
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Shape X position (pixels or percentage, default: '0%')"
                    },
                    "shape_y": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Shape Y position (pixels or percentage, default: '0%')"
                    },
                    "shape_width": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Shape width (pixels or percentage, default: '100%')"
                    },
                    "shape_height": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "string"}
                        ],
                        "description": "Shape height (pixels or percentage, default: '100%')"
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
                    "oneOf": [
                        {"type": "integer"},
                        {"type": "string"}
                    ],
                    "description": "Width of overlay area (pixels or percentage)"
                },
                "height": {
                    "oneOf": [
                        {"type": "integer"},
                        {"type": "string"}
                    ],
                    "description": "Height of overlay area (pixels or percentage)"
                },
                "x": {
                    "oneOf": [
                        {"type": "integer"},
                        {"type": "string"}
                    ],
                    "description": "X coordinate for overlay position (pixels or percentage, default: 0)"
                },
                "y": {
                    "oneOf": [
                        {"type": "integer"},
                        {"type": "string"}
                    ],
                    "description": "Y coordinate for overlay position (pixels or percentage, default: 0)"
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

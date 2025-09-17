from PIL import Image, ImageDraw, ImageFont

class Box:
    def __init__(self, width=None, height=None, 
                 layout="absolute",  # "row", "column", "absolute"
                 bg_color=(255, 255, 255, 0), 
                 padding=0, margin=0,
                 content=None):
        """
        width, height: fixed size or None (auto)
        layout: row | column | absolute
        content: ("text", str) | ("image", PIL.Image) | None
        """
        self.width = width
        self.height = height
        self.layout = layout
        self.bg_color = bg_color
        self.padding = padding
        self.margin = margin
        self.content = content
        self.children = []

    def add(self, child):
        """Add a child Box."""
        self.children.append(child)
        return child

    def compute_size(self, draw=None, font=None):
        """Compute size if auto, based on content + children."""
        if self.width is not None and self.height is not None:
            return self.width, self.height

        w, h = 0, 0
        if self.layout == "row":
            for c in self.children:
                cw, ch = c.compute_size(draw, font)
                w += cw
                h = max(h, ch)
        elif self.layout == "column":
            for c in self.children:
                cw, ch = c.compute_size(draw, font)
                h += ch
                w = max(w, cw)
        else:  # absolute
            for c in self.children:
                cw, ch = c.compute_size(draw, font)
                w = max(w, cw)
                h = max(h, ch)

        # Include content size
        if self.content:
            if self.content[0] == "text":
                text = self.content[1]
                font = font or ImageFont.load_default()
                try:
                    # New Pillow (>=10.0.0)
                    bbox = draw.textbbox((0, 0), text, font=font)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    # Older Pillow
                    tw, th = font.getsize(text)
                w = max(w, tw)
                h = max(h, th)
            elif self.content[0] == "image":
                img = self.content[1]
                w = max(w, img.width)
                h = max(h, img.height)

        return (self.width or w + 2*self.padding, 
                self.height or h + 2*self.padding)

    def render(self, draw, x, y, font=None):
        """Render the box at (x, y)."""
        w, h = self.compute_size(draw, font)

        # Background
        draw.rectangle([x, y, x+w, y+h], fill=self.bg_color)

        # Render content
        if self.content:
            if self.content[0] == "text":
                text = self.content[1]
                font = font or ImageFont.load_default()
                draw.text((x+self.padding, y+self.padding), text, fill="black", font=font)
            elif self.content[0] == "image":
                img = self.content[1]
                img_area = img.resize((w-2*self.padding, h-2*self.padding))
                draw.im.paste(img_area, (x+self.padding, y+self.padding))

        # Render children
        cur_x, cur_y = x + self.padding, y + self.padding
        for c in self.children:
            cw, ch = c.compute_size(draw, font)
            c.render(draw, cur_x, cur_y, font)
            if self.layout == "row":
                cur_x += cw
            elif self.layout == "column":
                cur_y += ch


# Example usage
if __name__ == "__main__":
    canvas = Image.new("RGBA", (600, 400), "white")
    draw = ImageDraw.Draw(canvas)

    root = Box(layout="row", bg_color=(220, 220, 220, 255), padding=10)
    left = root.add(Box(layout="column", bg_color=(255, 200, 200, 255), padding=5))
    right = root.add(Box(layout="column", bg_color=(200, 255, 200, 255), padding=5))

    left.add(Box(content=("text", "Hello World"), bg_color=(255, 255, 255, 255), padding=5))
    # left.add(Box(content=("text", "World!"), bg_color=(255, 255, 255, 255), padding=5))

    right.add(Box(content=("text", "Right side"), bg_color=(255, 255, 255, 255), padding=5))

    root.render(draw, 100, 100)
    canvas.show()
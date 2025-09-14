def hex_to_rgba(hex_str, alpha=255):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 8:
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        a = int(hex_str[6:8], 16)
        return (r, g, b, int(a * alpha / 255))
    elif len(hex_str) == 6:
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, alpha)
    elif len(hex_str) == 4:  # e.g. #affc
        r, g, b = [int(hex_str[i]*2, 16) for i in (0,1,2)]
        a = int(hex_str[3]*2, 16)
        return (r, g, b, a)
    else:
        r, g, b = [int(hex_str[i]*2, 16) for i in (0,1,2)]
        return (r, g, b, alpha)

def percent(val, maxval):
    if isinstance(val, str) and val.endswith('%'):
        return int((float(val[:-1]) / 100) * maxval)
    return int(val)

def get_anchor_pos(anchor, img_w, img_h, ele_w, ele_h):
    x = int(img_w * 0.5 - ele_w * 0.5)
    y = int(img_h * 0.5 - ele_h * 0.5)
    if anchor is None or anchor == 'top-left':
        return 0, 0
    if anchor == 'center':
        return x, y
    if anchor == 'top-center':
        return x, 0
    if anchor == 'center-left':
        return 0, y
    if anchor == 'center-right':
        return img_w - ele_w, y
    if anchor == 'bottom-left':
        return 0, img_h - ele_h
    if anchor == 'bottom-center':
        return x, img_h - ele_h
    if anchor == 'bottom-right':
        return img_w - ele_w, img_h - ele_h
    return 0, 0
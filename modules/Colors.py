White = (255, 255, 255)
Black = (0, 0, 0)
Red = (255, 0, 0)
Blue = (0, 0, 255)

def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """
    Converts a hex color string (e.g., '#7a8eb9' or '7a8eb9') to an RGB tuple.
    """
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
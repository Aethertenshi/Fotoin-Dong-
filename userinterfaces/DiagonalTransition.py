import pygame
from modules import Colors
from pygame import draw

class DiagonalTransition:
    GRID_SIZE = 50

    def __init__(self, grid_size=None):
        """
        Initializes an instance of the DiagonalTransition class.
        
        Parameters:
        - grid_size: Custom size of the grid blocks. Defaults to GRID_SIZE class attribute.
        """
        self.grid_size = grid_size if grid_size is not None else DiagonalTransition.GRID_SIZE

    def DrawTransition(self, screen, monitor, progress=1.0, mode="top_to_bottom", color=Colors.Black):
        """
        Draws a screen transition effect.
        
        Parameters:
        - screen: The PyGame surface to draw on.
        - monitor: The monitor info object (containing current_w, current_h).
        - progress: A float from 0.0 to 1.0 indicating how far along the transition is.
        - mode: The type of transition ("top_to_bottom", "bottom_to_top", "diagonal", "fade_in", "fade_out").
        - color: The RGB color tuple of the transition.
        """
        # Clamp progress between 0.0 and 1.0
        progress = max(0.0, min(1.0, progress))
        
        width = monitor.current_w
        height = monitor.current_h
        grid_size = self.grid_size
        
        # Performance optimization: if fully opaque (progress = 1.0) and not fading out,
        # fill the entire screen immediately and skip cell loops.
        if progress >= 1.0 and mode != "fade_out":
            temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            temp_surface.fill(color)
            screen.blit(temp_surface, (0, 0))
            return

        # Early exits for transparent states
        if mode == "fade_out" and progress >= 1.0:
            return
        if mode != "fade_out" and progress <= 0.0:
            return
            
        temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        if mode == "fade_in":
            alpha = int(progress * 255)
            temp_surface.fill((*color, alpha))
            
        elif mode == "fade_out":
            alpha = int((1.0 - progress) * 255)
            temp_surface.fill((*color, alpha))
            
        elif mode == "top_to_bottom":
            cols = list(range(0, width, grid_size))
            rows = list(range(0, height, grid_size))
            max_y = rows[-1] if rows else 1
            
            for x in cols:
                for y in rows:
                    # Mathematically safe normalization (always <= 1.0)
                    y_norm = y / max_y
                    cell_t = max(0.0, min(1.0, (progress - y_norm * 0.7) / 0.3))
                    alpha = int(cell_t * 255)
                    
                    if alpha > 0:
                        w = int(cell_t * grid_size)
                        h = int(cell_t * grid_size)
                        offset_x = (grid_size - w) // 2
                        offset_y = (grid_size - h) // 2
                        draw.rect(temp_surface, (*color, alpha), (x + offset_x, y + offset_y, w, h))
                        
        elif mode == "bottom_to_top":
            cols = list(range(0, width, grid_size))
            rows = list(range(0, height, grid_size))
            max_y = rows[-1] if rows else 1
            
            for x in cols:
                for y in rows:
                    y_norm = (max_y - y) / max_y
                    cell_t = max(0.0, min(1.0, (progress - y_norm * 0.7) / 0.3))
                    alpha = int(cell_t * 255)
                    
                    if alpha > 0:
                        w = int(cell_t * grid_size)
                        h = int(cell_t * grid_size)
                        offset_x = (grid_size - w) // 2
                        offset_y = (grid_size - h) // 2
                        draw.rect(temp_surface, (*color, alpha), (x + offset_x, y + offset_y, w, h))
                        
        elif mode == "diagonal":
            cols = list(range(0, width, grid_size))
            rows = list(range(0, height, grid_size))
            max_x = cols[-1] if cols else 1
            max_y = rows[-1] if rows else 1
            max_dist = max(1, max_x + max_y)
            
            for x in cols:
                for y in rows:
                    dist_norm = (x + y) / max_dist
                    cell_t = max(0.0, min(1.0, (progress - dist_norm * 0.7) / 0.3))
                    alpha = int(cell_t * 255)
                    
                    if alpha > 0:
                        w = int(cell_t * grid_size)
                        h = int(cell_t * grid_size)
                        offset_x = (grid_size - w) // 2
                        offset_y = (grid_size - h) // 2
                        draw.rect(temp_surface, (*color, alpha), (x + offset_x, y + offset_y, w, h))
                        
        screen.blit(temp_surface, (0, 0))
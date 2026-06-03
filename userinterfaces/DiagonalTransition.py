import pygame
from modules import Colors
from pygame import draw, display

# ==== Variables ===
GRID_SIZE = 50

def DrawTransition(screen, monitor):
    for x in range(0, monitor.current_w, GRID_SIZE):
        for y in range(0, monitor.current_h, GRID_SIZE):
            draw.rect(screen, Colors.Black, (x, y, GRID_SIZE, GRID_SIZE))
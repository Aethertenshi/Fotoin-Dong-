import pygame, sys
from modules import Colors, easings
from userinterfaces import DiagonalTransition
from pygame import draw, display, event

pygame.init()

# === Game Variables ===


# === Game Initialization ===
monitor = display.Info()
screen = display.set_mode(size=(monitor.current_w, monitor.current_h), vsync=True, flags=pygame.NOFRAME)
display.set_caption("Fotoin Dong - ArtFrameEXT")

DiagonalTransition.GRID_SIZE = 50

tween = easings.Tween()
tween.Start()

# === Game Loop ===
_running = True
while (_running):
    for ev in event.get():
        if ev.type == pygame.QUIT:
            _running = False

    screen.fill(Colors.White)
    draw.rect(screen, Colors.Red, (50, 50, 200, 200))

    DiagonalTransition.DrawTransition(screen, monitor)

    display.flip()

pygame.quit()
sys.exit()
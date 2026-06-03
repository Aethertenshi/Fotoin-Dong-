import pygame, sys
import os, random
from modules import Colors
from modules.easings import Tween, Easings, Direction
from modules.Sprite import TransformSprite
from userinterfaces import DiagonalTransition
from pygame import draw, display, event, mixer, font

pygame.init()
mixer.init()
font.init()

# === Game Global Setup ===
MENU_VISIBLE_MILIS = 2
BEAT_INTERVAL_MS = 345
BASE_SCALE = 0.5
BEAT_STRENGTH = 0.03

# Background slide config
BG_TRANSITION_DURATION = 3  # transition duration
BG_SLIDE_INTERVAL = 0     # transition every 1 second
THEME_COLOR = Colors.hex_to_rgb("7a8eb9")

# === Game Initialization ===
monitor = display.Info()
screen = display.set_mode(size=(monitor.current_w, monitor.current_h), vsync=True, flags=pygame.NOFRAME)
display.set_caption("Fotoin Dong - ArtFrameEXT")

# Instantiate transitions
DiagonalTransition.GRID_SIZE = 50
intro_transition = DiagonalTransition()
bg_transition = DiagonalTransition()

# === Sound Initialization ===
mixer.music.load("sounds/main.mp3")
mixer.music.play(start=2)

# === Sprite Setup ===
logoBiasa = TransformSprite(
    image_path="textures/FOTOINDONG_BIASA.png",
    x=monitor.current_w // 2,
    y=monitor.current_h // 2,
)
logoMono = TransformSprite(
    image_path="textures/FOTOINDONG_MONO.png",
    x=monitor.current_w // 2,
    y=monitor.current_h // 2,
)
camera = TransformSprite(
    image_path="textures/camera.png",
    x=150,
    y=monitor.current_h - 150,
)
sparkle = TransformSprite(
    image_path="textures/sparkle.png",
    x=monitor.current_w - 150,
    y=150,
)
mascot = TransformSprite(
    image_path="textures/FOTOINDONG_MONO.png",
    x=monitor.current_w - 220,
    y=monitor.current_h - 220,
)

# Load all background places images dynamically
places_dir = "places"
bg_paths = sorted([os.path.join(places_dir, f) for f in os.listdir(places_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
bg_sprites = [TransformSprite(path, monitor.current_w // 2, monitor.current_h // 2) for path in bg_paths]
current_bg_index = 0
next_bg_index = 0
is_bg_transitioning = False
is_intro_done = False
bg_timer = 0.0

# === State variables ===
transition_progress = 1.0
isMenuVisible = False

# Intro screen transition progress callback
def on_update_progress(val):
    global transition_progress
    transition_progress = val
tween = Tween(on_update=on_update_progress)

# Logo Mono fade-in progress callback
logo_fade_progress = 0.0
def on_update_logo_fade(val):
    global logo_fade_progress
    logo_fade_progress = val
logo_fade_tween = Tween(on_update=on_update_logo_fade)

# Background slide transition callback
bg_transition_progress = 0.0
def on_update_bg_transition(val):
    global bg_transition_progress
    bg_transition_progress = val

def on_bg_transition_complete():
    global current_bg_index, is_bg_transitioning
    current_bg_index = next_bg_index
    is_bg_transitioning = False

bg_tween = Tween(on_update=on_update_bg_transition, on_complete=on_bg_transition_complete)

def start_menu_transition():
    tween.Start(
        duration=3,
        startValue=1.0,
        endValue=0.0,
        easing=Easings.Cubic,
        direction=Direction.Out
    )

# Setup font for interactive UI
myfont = font.SysFont("Arial", 24)
title_font = font.SysFont("Arial", 28, bold=True)

# === Pre-Run Setters ===
logoBiasa.scale = BASE_SCALE
logoMono.scale = 0.5
logoMono.alpha = 0.0  # Start fully transparent
camera.scale = 0.4
camera.alpha = 0.0
camera.rotation = -45.0
sparkle.scale = 0.4
sparkle.alpha = 0.0
sparkle.rotation = 180.0

# Start the logo fade-in animation immediately
logo_fade_tween.Start(
    duration=MENU_VISIBLE_MILIS / 2,
    startValue=0.0,
    endValue=1.0,
    easing=Easings.Quad,
    direction=Direction.In
)

# === Game Loop ===
clock = pygame.time.Clock()
_running = True

while (_running):
    dt = clock.tick(60) / 1000.0
    tween.Update(dt)
    logo_fade_tween.Update(dt)
    bg_tween.Update(dt)

    # Event handling
    for ev in event.get():
        if ev.type == pygame.QUIT:
            _running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                _running = False

    if (transition_progress < 0.01 and not is_intro_done):
        is_intro_done = True

    # Background slideshow logic (only runs after intro is done)
    if is_intro_done and not is_bg_transitioning:
        bg_timer += dt
        if bg_timer >= BG_SLIDE_INTERVAL:
            bg_timer = 0.0
            is_bg_transitioning = True
            next_bg_index = (current_bg_index + 1) % len(bg_sprites)
            # Start background transition (0.0 to 1.0) and explicitly reset progress to prevent 1-frame state lag
            bg_transition_progress = 0.0
            bg_tween.Start(
                duration=BG_TRANSITION_DURATION,
                startValue=0.0,
                endValue=1.0,
                easing=Easings.Cubic,
                direction=Direction.Out
            )


    if ((mixer.music.get_pos() / 1000) > MENU_VISIBLE_MILIS and not isMenuVisible):
        start_menu_transition()
        isMenuVisible = True

    # Calculate logoMono alpha dynamically
    if not isMenuVisible:
        logoMono.alpha = logo_fade_progress * 255
    else:
        logoMono.alpha = transition_progress * 255
        
    # Calculate logoBiasa beat scale dynamically based on music position
    music_time = max(0.0, mixer.music.get_pos() / 1000.0)
    beat_sec = BEAT_INTERVAL_MS / 1000.0
    if beat_sec > 0:
        beat_phase = (music_time % beat_sec) / beat_sec
        # Cubic decay for a punchy beat pulse
        decay = (1.0 - beat_phase) ** 3.0
        logoBiasa.scale = BASE_SCALE + BEAT_STRENGTH * decay
    else:
        logoBiasa.scale = BASE_SCALE

    # Calculate position and alpha for camera and sparkle (decorations)
    # They fade and slide in from outside the screen bounds as the intro transition clears
    sparkle_target_x = monitor.current_w - 50
    sparkle_target_y = 50
    sparkle.x = sparkle_target_x + 350 * transition_progress
    sparkle.y = sparkle_target_y - 350 * transition_progress
    sparkle.alpha = (1.0 - transition_progress) * 255

    camera_target_x = 50
    camera_target_y = monitor.current_h - 50
    camera.x = camera_target_x - 350 * transition_progress
    camera.y = camera_target_y + 350 * transition_progress
    camera.alpha = (1.0 - transition_progress) * 255

    # Draw background slideshow
    if is_bg_transitioning:
        if bg_transition_progress < 0.45:
            # Phase 1: Sweep in (progress goes 0.0 to 1.0)
            if bg_sprites:
                bg_sprites[current_bg_index].draw(screen, cover=True)
            p_in = bg_transition_progress / 0.45
            bg_transition.DrawTransition(screen, monitor, p_in, "diagonal", THEME_COLOR)
        elif bg_transition_progress <= 0.55:
            # Crossover Plateau: Keep fully covered with solid color to safely swap image behind it
            if bg_sprites:
                bg_sprites[next_bg_index].draw(screen, cover=True)
            bg_transition.DrawTransition(screen, monitor, 1.0, "diagonal", THEME_COLOR)
        else:
            # Phase 2: Sweep out (progress goes 1.0 to 0.0)
            if bg_sprites:
                bg_sprites[next_bg_index].draw(screen, cover=True)
            p_out = (bg_transition_progress - 0.55) / 0.45
            bg_transition.DrawTransition(screen, monitor, 1.0 - p_out, "diagonal", THEME_COLOR)
    else:
        # Static state
        if bg_sprites:
            bg_sprites[current_bg_index].draw(screen, cover=True)
    
    # Draw the Transformable Sprite
    logoBiasa.draw(screen)

    # Draw camera and sparkle decorations (drawn before intro_transition so they hide under it)
    camera.draw(screen)
    sparkle.draw(screen)

    # Draw the screen transition overlay on top
    intro_transition.DrawTransition(screen, monitor, transition_progress, "diagonal")

    # Draw Mono Logo
    logoMono.draw(screen)
    
    display.flip()

pygame.quit()
sys.exit()
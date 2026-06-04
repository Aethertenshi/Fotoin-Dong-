import pygame, sys
import os, random, math, time
from modules import Colors
from modules.easings import Tween, Easings, Direction
from modules.Sprite import TransformSprite
from userinterfaces import DiagonalTransition
from modules.Gestures import GestureManager
from pygame import draw, display, event, mixer, font

pygame.init()
mixer.init()
font.init()

# === Game Global Setup ===
MENU_VISIBLE_MILIS = 2
BEAT_INTERVAL_MS = 348
BASE_SCALE = 0.5
BEAT_STRENGTH = 0.03

# Background slide config
BG_TRANSITION_DURATION = 3  # transition duration
BG_SLIDE_INTERVAL = 1.0       # transition every 1 second
THEME_COLOR = Colors.hex_to_rgb("7a8eb9")

# === Game Initialization ===
monitor = display.Info()
screen = display.set_mode(size=(monitor.current_w, monitor.current_h), vsync=True, flags=pygame.NOFRAME)
display.set_caption("Fotoin Dong - ArtFrameEXT")

# Instantiate transitions
DiagonalTransition.GRID_SIZE = 50
intro_transition = DiagonalTransition()
bg_transition = DiagonalTransition()

# === Hand Tracker Setup ===
gesture_mgr = GestureManager()
gesture_mgr.start()

# === Sound Initialization ===
mixer.music.load("sounds/main.mp3")
mixer.music.play(start=2)
# Set initial music volume to 1.0
mixer.music.set_volume(1.0)

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
    x=50,
    y=monitor.current_h - 50,
)
sparkle = TransformSprite(
    image_path="textures/sparkle.png",
    x=monitor.current_w - 50,
    y=50,
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
myfont = font.SysFont("Arial", 20)
title_font = font.SysFont("Arial", 24, bold=True)

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
    easing=Easings.Cubic,
    direction=Direction.Out
)

# === Cute Game Loop Variables ===
game_stages = [
    {"text": "Selamat datang di Fotoin Dong! Kepalkan tanganmu di depan kamera untuk memulai.", "target": None},
    {"text": "Cari kota dengan gedung pencakar langit. Jepit telunjuk dan jempol kiri untuk mengganti slide. Buat bentuk bingkai foto dengan tanganmu untuk memotretnya!", "target": "places/sunset city with sky scrapers.jpg"},
    {"text": "Cari matahari terbenam di laut dengan awan abu-abu. Jepit jari tangan kirimu untuk mencari, lalu bingkai fotonya!", "target": "places/sea sunset with grey clouds.jpg"},
    {"text": "Cari laut dengan seseorang yang sedang berdiri. Bingkai fotonya!", "target": "places/sea with a person standing.jpg"},
    {"text": "Cari laut dengan awan putih. Sedikit lagi, bingkai fotonya!", "target": "places/sea with white clouds.jpg"},
    {"text": "Cari matahari terbenam dengan pepohonan. Bingkai fotonya!", "target": "places/sunset with trees.jpg"},
    {"text": "Cari matahari terbenam dengan dua jembatan. Tunjukkan hasil jepretan bingkai terakhirmu!", "target": "places/sunset with two bridge.jpg"},
    {"text": "Permainan selesai! Kamu berhasil mengabadikan semua lokasi. Kepalkan tanganmu untuk bermain lagi.", "target": None}
]
current_stage = 0
last_active_gesture = None

# Timer overlays
flash_timer = 0.0
success_timer = 0.0
warning_timer = 0.0
feedback_text = ""

# Chat UI Variables
chat_history = []
chat_alpha = 0.0
elements_alpha = 0.0

# === UI Helper Drawing Functions ===

def wrap_text(text, max_w):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if myfont.size(test_line)[0] < max_w:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    return lines

def draw_bubble(surface, color, x, y, w, h, is_left):
    # Draw the main rounded rectangle
    draw.rect(surface, color, (x, y, w, h), border_radius=12)
    draw.rect(surface, (220, 220, 220, 245), (x, y, w, h), width=1, border_radius=12)
    
    # Draw the tail
    if is_left:
        # Left bubble tail: triangle pointing left
        points = [
            (x, y + 10),
            (x - 8, y + 15),
            (x, y + 20)
        ]
        draw.polygon(surface, color, points)
        draw.line(surface, (220, 220, 220, 245), (x - 8, y + 15), (x, y + 10), 1)
        draw.line(surface, (220, 220, 220, 245), (x - 8, y + 15), (x, y + 20), 1)
        # Erase seam border
        draw.line(surface, color, (x, y + 11), (x, y + 19), 2)
    else:
        # Right bubble tail: triangle pointing right
        points = [
            (x + w, y + 10),
            (x + w + 8, y + 15),
            (x + w, y + 20)
        ]
        draw.polygon(surface, color, points)
        draw.line(surface, (220, 220, 220, 245), (x + w + 8, y + 15), (x + w, y + 10), 1)
        draw.line(surface, (220, 220, 220, 245), (x + w + 8, y + 15), (x + w, y + 20), 1)
        # Erase seam border
        draw.line(surface, color, (x + w, y + 11), (x + w, y + 19), 2)

def draw_chat_window(screen, width, height, alpha):
    if alpha <= 0:
        return
        
    # Create a semi-transparent surface for the entire chat panel
    chat_panel = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # 1. Main Background: Clean soft translucent grey/white
    draw.rect(chat_panel, (245, 245, 245, 225), (0, 0, width, height), border_radius=18)
    draw.rect(chat_panel, (220, 220, 220, 255), (0, 0, width, height), width=2, border_radius=18)
    
    # 2. Draw Message Area (clipped)
    msg_area_h = height - 130
    msg_surface = pygame.Surface((width, msg_area_h), pygame.SRCALPHA)
    
    # Calculate layout positions
    layout_heights = []
    total_content_height = 0
    for msg in chat_history:
        h = 0
        if msg["type"] == "text":
            lines = wrap_text(msg["content"], 300)
            h = len(lines) * 24 + 30
        elif msg["type"] == "image":
            h = 112 + 20
        layout_heights.append(h)
        total_content_height += h + 15
        
    start_y = 20
    if total_content_height > msg_area_h - 40:
        start_y = (msg_area_h - 40) - total_content_height
        
    current_y = start_y
    for i, msg in enumerate(chat_history):
        msg_h = layout_heights[i]
        
        # Only draw if visible
        if current_y + msg_h > 0 and current_y < msg_area_h:
            bubble_color = (255, 255, 255, 245)
            
            if msg["sender"] == "assistant":
                # Left Bubble (Guide)
                bubble_w = 340
                draw_bubble(msg_surface, bubble_color, 25, current_y, bubble_w, msg_h, is_left=True)
                
                # Draw Text
                lines = wrap_text(msg["content"], bubble_w - 40)
                text_y = current_y + 15
                for line in lines:
                    text_surf = myfont.render(line.strip(), True, (60, 60, 60))
                    msg_surface.blit(text_surf, (45, text_y))
                    text_y += 24
                    
            elif msg["sender"] == "player":
                # Right Bubble (Player Photo / Text)
                bubble_w = 220
                x_pos = width - bubble_w - 25
                draw_bubble(msg_surface, bubble_color, x_pos, current_y, bubble_w, msg_h, is_left=False)
                
                if msg["type"] == "image":
                    msg_surface.blit(msg["content"], (x_pos + 10, current_y + 10))
                elif msg["type"] == "text":
                    lines = wrap_text(msg["content"], bubble_w - 40)
                    text_y = current_y + 15
                    for line in lines:
                        text_surf = myfont.render(line.strip(), True, (60, 60, 60))
                        msg_surface.blit(text_surf, (x_pos + 20, text_y))
                        text_y += 24
                    
        current_y += msg_h + 15
        
    chat_panel.blit(msg_surface, (0, 70))
    
    # 3. Header Bar
    draw.rect(chat_panel, (255, 255, 255, 255), (0, 0, width, 70), border_top_left_radius=18, border_top_right_radius=18)
    draw.line(chat_panel, (220, 220, 220, 255), (0, 70), (width, 70), 1)
    
    # Draw avatar using logoMono
    avatar_center = (40, 35)
    avatar_radius = 20
    draw.circle(chat_panel, (230, 230, 230), avatar_center, avatar_radius)
    if 'logoMono' in globals():
        avatar_img = pygame.transform.scale(logoMono.original_image, (32, 32))
        avatar_rect = avatar_img.get_rect(center=avatar_center)
        chat_panel.blit(avatar_img, avatar_rect)
        
    # Title & Online status
    name_surf = title_font.render("Guru Seni Budaya", True, (40, 40, 40))
    chat_panel.blit(name_surf, (75, 12))
    
    draw.circle(chat_panel, (76, 175, 80), (80, 48), 5)
    status_font = font.SysFont("Arial", 14)
    status_surf = status_font.render("online", True, (120, 120, 120))
    chat_panel.blit(status_surf, (92, 41))
    
    # Aesthetics camera icon
    cam_x = width - 45
    cam_y = 28
    draw.rect(chat_panel, (100, 110, 120), (cam_x, cam_y, 16, 12), border_radius=2)
    draw.polygon(chat_panel, (100, 110, 120), [(cam_x + 16, cam_y + 3), (cam_x + 21, cam_y), (cam_x + 21, cam_y + 11), (cam_x + 16, cam_y + 8)])
    
    # 4. Bottom Input Bar
    draw.rect(chat_panel, (255, 255, 255, 255), (0, height - 60, width, 60), border_bottom_left_radius=18, border_bottom_right_radius=18)
    draw.line(chat_panel, (220, 220, 220, 255), (0, height - 60), (width, height - 60), 1)
    
    placeholder_font = font.SysFont("Arial", 16, italic=True)
    placeholder_surf = placeholder_font.render("Type a message...", True, (160, 160, 160))
    chat_panel.blit(placeholder_surf, (20, height - 40))
    
    clip_x = width - 35
    clip_y = height - 30
    draw.line(chat_panel, (120, 130, 140), (clip_x, clip_y - 8), (clip_x, clip_y + 8), 2)
    draw.line(chat_panel, (120, 130, 140), (clip_x - 8, clip_y), (clip_x + 8, clip_y), 2)
    
    chat_panel.set_alpha(int(alpha))
    screen.blit(chat_panel, (50, 50))

def draw_hand_preview(screen, landmarks, x, y, size):
    # Preview background box (simple white)
    draw.rect(screen, (255, 255, 255, 220), (x, y, size, size), border_radius=15)
    draw.rect(screen, (230, 230, 230, 220), (x, y, size, size), width=2, border_radius=15)
    
    for hand in landmarks:
        points = []
        for lm in hand:
            px = x + int(lm[0] * size)
            py = y + int(lm[1] * size)
            points.append((px, py))
            draw.circle(screen, (255, 105, 180), (px, py), 5)  # Pink joint dot
            
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (9, 10), (10, 11), (11, 12),
            (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17)
        ]
        for conn in connections:
            if conn[0] < len(points) and conn[1] < len(points):
                draw.line(screen, (255, 192, 203), points[conn[0]], points[conn[1]], 3)  # Cute light pink bones

# === Game Loop ===
clock = pygame.time.Clock()
_running = True

while (_running):
    dt = clock.tick(60) / 1000.0
    tween.Update(dt)
    logo_fade_tween.Update(dt)
    bg_tween.Update(dt)
    
    # Update background slideshow timer only during the welcome stage (stage 0)
    if is_intro_done and current_stage == 0:
        if not is_bg_transitioning:
            bg_timer += dt
            if bg_timer >= BG_SLIDE_INTERVAL:
                is_bg_transitioning = True
                next_bg_index = (current_bg_index + 1) % len(bg_sprites)
                bg_transition_progress = 0.0
                bg_tween.Start(BG_TRANSITION_DURATION, 0.0, 1.0, Easings.Quad, Direction.InOut)
                bg_timer = 0.0
    else:
        bg_timer = 0.0

    # Handle timers
    if flash_timer > 0:
        flash_timer -= dt
    if success_timer > 0:
        success_timer -= dt
    if warning_timer > 0:
        warning_timer -= dt

    # Handle chat window fade-in / fade-out alpha
    if current_stage > 0:
        chat_alpha = min(255.0, chat_alpha + 400.0 * dt)
    else:
        chat_alpha = max(0.0, chat_alpha - 400.0 * dt)

    # Event handling
    for ev in event.get():
        if ev.type == pygame.QUIT:
            _running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                _running = False

    # Get gesture from background manager
    active_gesture = gesture_mgr.detected_gesture
    trigger_gesture = None
    if active_gesture != last_active_gesture:
        if active_gesture is not None:
            trigger_gesture = active_gesture
        last_active_gesture = active_gesture

    if (transition_progress < 0.01 and not is_intro_done):
        is_intro_done = True

    # === Gesture State Routing ===
    if is_intro_done:
        if current_stage == 0:
            # Welcome Stage
            if trigger_gesture == "fist":
                # Start game: turn down volume and go to level 1
                mixer.music.set_volume(0.2)
                current_stage = 1
                is_bg_transitioning = False  # Reset/cancel any active welcome transition
                current_bg_index = 0
                chat_history.clear()
                chat_history.append({"sender": "assistant", "type": "text", "content": game_stages[current_stage]["text"]})
                
        elif current_stage in [1, 2, 3, 4, 5, 6]:
            # Slideshow Searching Stages
            # Left-hand pinch (immediate cycle)
            if trigger_gesture == "pinch":
                current_bg_index = (current_bg_index + 1) % len(bg_sprites)
            
            # Check for Photo Frame Capture Gesture
            elif trigger_gesture == "frame" and success_timer <= 0:
                current_path = bg_paths[current_bg_index].replace('\\', '/')
                target_path = game_stages[current_stage]["target"]
                
                # Capture current slide as thumbnail
                orig_img = bg_sprites[current_bg_index].original_image
                thumb = pygame.transform.scale(orig_img, (200, 112))
                
                # Always trigger a camera flash and add the photo to the chat
                flash_timer = 0.4
                chat_history.append({"sender": "player", "type": "image", "content": thumb})
                
                if current_path == target_path:
                    success_timer = 1.8
                    feedback_text = "Nice shot! Target photo matched."
                    chat_history.append({"sender": "assistant", "type": "text", "content": feedback_text})
                else:
                    warning_timer = 1.8
                    feedback_text = "That's not the correct location. Keep searching!"
                    chat_history.append({"sender": "assistant", "type": "text", "content": feedback_text})
                        
            # Advance stage after success timer completes
            if success_timer > 0 and success_timer <= dt:
                current_stage += 1
                if current_stage <= 7:
                    chat_history.append({"sender": "assistant", "type": "text", "content": game_stages[current_stage]["text"]})
                
        elif current_stage == 7:
            # Outro/Finish Stage
            if trigger_gesture == "fist":
                # Restart: turn music volume back up
                mixer.music.set_volume(1.0)
                current_stage = 0
                current_bg_index = 0
                next_bg_index = 0

    if ((mixer.music.get_pos() / 1000) > MENU_VISIBLE_MILIS and not isMenuVisible):
        start_menu_transition()
        isMenuVisible = True

    # Calculate logoMono alpha dynamically
    if not isMenuVisible:
        logoMono.alpha = logo_fade_progress * 255
        logoMono.scale = pygame.math.lerp(0.025, 1, 1-(logo_fade_progress*.5)) #math.ler(1 - (logo_fade_progress), 0.5)
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

    # Calculate elements_alpha and positions for welcome sprites (logoBiasa, camera, sparkle)
    if not is_intro_done:
        elements_alpha = (1.0 - transition_progress) * 255.0
        
        # Slide in from outside the screen bounds
        sparkle_target_x = monitor.current_w - 30
        sparkle_target_y = 30
        sparkle.x = sparkle_target_x + 350 * transition_progress
        sparkle.y = sparkle_target_y - 350 * transition_progress
        
        camera_target_x = 30
        camera_target_y = monitor.current_h - 30
        camera.x = camera_target_x - 350 * transition_progress
        camera.y = camera_target_y + 350 * transition_progress
    else:
        if current_stage == 0:
            elements_alpha = min(255.0, elements_alpha + 400.0 * dt)
            sparkle.x = monitor.current_w - 30
            sparkle.y = 30
            camera.x = 30
            camera.y = monitor.current_h - 30
        else:
            elements_alpha = max(0.0, elements_alpha - 400.0 * dt)
            # Slide back out off-screen as they fade
            slide_out_progress = (255.0 - elements_alpha) / 255.0
            
            sparkle.x = (monitor.current_w - 30) + 350 * slide_out_progress
            sparkle.y = 30 - 350 * slide_out_progress
            
            camera.x = 30 - 350 * slide_out_progress
            camera.y = (monitor.current_h - 30) + 350 * slide_out_progress

    # Apply alpha to sprites
    logoBiasa.alpha = elements_alpha
    camera.alpha = elements_alpha
    sparkle.alpha = elements_alpha

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
            
    # Draw simple white chat panel on the left
    if is_intro_done:
        draw_chat_window(screen, 460, monitor.current_h - 100, chat_alpha)
        
        # Draw Mini Hand Preview
        draw_hand_preview(screen, gesture_mgr.landmarks, monitor.current_w - 240, 40, 180)
    
    # Draw the Transformable Sprite (as long as it is visible)
    if elements_alpha > 0.0:
        logoBiasa.draw(screen)

    # Draw camera and sparkle decorations (drawn before intro_transition so they hide under it, as long as visible)
    if elements_alpha > 0.0:
        camera.draw(screen)
        sparkle.draw(screen)

    # Draw the screen transition overlay on top
    intro_transition.DrawTransition(screen, monitor, transition_progress, "diagonal")

    # Draw Mono Logo
    logoMono.draw(screen)
    
    # Draw Camera Flash effect
    if flash_timer > 0:
        flash_surf = pygame.Surface((monitor.current_w, monitor.current_h))
        flash_surf.fill((255, 255, 255))
        flash_surf.set_alpha(int((flash_timer / 0.4) * 255))
        screen.blit(flash_surf, (0, 0))
    
    display.flip()

# Cleanup gesture background thread
gesture_mgr.stop()
pygame.quit()
sys.exit()
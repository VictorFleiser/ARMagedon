import cv2
import mediapipe as mp
import pygame
import numpy as np
import math
import time
import random

# --- Game Constants ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
SAFE_ZONE_PADDING_X = int(WINDOW_WIDTH * 0.1)
SAFE_ZONE_PADDING_Y = int(WINDOW_HEIGHT * 0.1)
SAFE_ZONE_RECT = pygame.Rect(
    SAFE_ZONE_PADDING_X,
    SAFE_ZONE_PADDING_Y,
    WINDOW_WIDTH - SAFE_ZONE_PADDING_X * 2,
    WINDOW_HEIGHT - SAFE_ZONE_PADDING_Y * 2
)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# --- Player and Bullet Config ---
PLAYER_RADIUS = 8
PLAYER_MOVE_SPEED = 100 # pixels per frame
BULLET_RADIUS = 10
BULLET_SPEED = 16
BULLETS_PER_RING = 12
MAXIMUM_BULLET_SPEED = 64

# --- Gameplay Dynamics ---
GRACE_PERIOD = 5 # seconds
INITIAL_BULLET_SPAWN_RATE = 2.0 # seconds
MINIMUM_SPAWN_RATE = 0.1 # The fastest the bullets will ever spawn (0.1s = 10 bullets/second)
SPAWN_RATE_ACCELERATION = 0.95 # Multiplier applied each spawn, smaller is faster acceleration
BULLET_SPEED_ACCELERATION = 1.02 # Multiplier applied to bullet speed each spawn

# --- MediaPipe Initialization ---
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

def calculate_hand_center(hand_landmarks, frame_dimensions):
    """Computes a stable hand center based on palm geometry."""
    if not hand_landmarks:
        return None
    
    width, height = frame_dimensions[1], frame_dimensions[0]
    
    wrist = hand_landmarks.landmark[0]
    
    # MCP joints (base of fingers)
    mcp_indices = [5, 9, 13, 17]
    mcp_points = [hand_landmarks.landmark[i] for i in mcp_indices]
    
    # Average of the MCPs
    avg_mcp_x = np.mean([p.x for p in mcp_points])
    avg_mcp_y = np.mean([p.y for p in mcp_points])
    
    # Midpoint between wrist and finger base average
    center_x = (wrist.x + avg_mcp_x) / 2.0 * width
    center_y = (wrist.y + avg_mcp_y) / 2.0 * height
    
    return int(center_x), int(center_y)

def calculate_centroid(landmark_list, frame_dimensions, is_hand=False):
    """Calculates either the mean centroid or palm-based center if it's a hand."""
    if not landmark_list:
        return None
    if is_hand:
        return calculate_hand_center(landmark_list, frame_dimensions)
    else:
        # Default mean centroid (used for face)
        x_coords = [lm.x for lm in landmark_list.landmark]
        y_coords = [lm.y for lm in landmark_list.landmark]
        centroid_x = np.mean(x_coords) * frame_dimensions[1]
        centroid_y = np.mean(y_coords) * frame_dimensions[0]
        return int(centroid_x), int(centroid_y)

def calculate_distance(point1, point2):
    """Calculates the Euclidean distance between two points."""
    return math.sqrt((point2.x - point1.x)**2 + (point2.y - point1.y)**2)

def is_hand_closed(hand_landmarks):
    """
    Checks if a hand is closed by calculating the distance between fingertips and the palm.
    A smaller total distance indicates a closed hand.
    """
    if not hand_landmarks:
        return False

    # Landmarks for fingertips
    fingertips = [
        # hand_landmarks.landmark[mp_holistic.HandLandmark.THUMB_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.INDEX_FINGER_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.MIDDLE_FINGER_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.RING_FINGER_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.PINKY_TIP],
    ]

    # Landmark for the base of the palm
    palm_base = hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST]

    total_distance = sum(calculate_distance(tip, palm_base) for tip in fingertips)
    
    # This threshold may need adjustment for different hand sizes and camera distances
    return total_distance < 0.7 

def draw_hand_landmarks(screen, results, frame_dimensions, colors, alpha=60, line_thickness=3, point_radius=6):
    """Draws semi-transparent hand landmarks and connecting lines using the players' colors."""
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    width, height = frame_dimensions[1], frame_dimensions[0]
    
    def draw_single_hand(landmarks, color):
        if not landmarks:
            return
        
        # Draw connections (finger bones)
        for connection in mp.solutions.holistic.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start = landmarks.landmark[start_idx]
            end = landmarks.landmark[end_idx]
            start_xy = (int(start.x * width), int(start.y * height))
            end_xy = (int(end.x * width), int(end.y * height))
            pygame.draw.line(overlay, (*color, alpha), start_xy, end_xy, line_thickness)
        
        # Draw the landmark points (joints)
        for lm in landmarks.landmark:
            x, y = int(lm.x * width), int(lm.y * height)
            pygame.draw.circle(overlay, (*color, alpha), (x, y), point_radius)
    
    # Draw hands if detected
    if results.left_hand_landmarks:
        draw_single_hand(results.left_hand_landmarks, colors.get("left", (0, 255, 0)))
        if is_hand_closed(results.left_hand_landmarks):
            pygame.draw.circle(overlay, (255, 0, 0, 128), calculate_hand_center(results.left_hand_landmarks, frame_dimensions), PLAYER_RADIUS + 10)
    if results.right_hand_landmarks:
        draw_single_hand(results.right_hand_landmarks, colors.get("right", (0, 255, 0)))
        if is_hand_closed(results.right_hand_landmarks):
            pygame.draw.circle(overlay, (255, 0, 0, 128), calculate_hand_center(results.right_hand_landmarks, frame_dimensions), PLAYER_RADIUS + 10)
    
    # Optional: draw face landmarks (simplified)
    if results.face_landmarks and "face" in colors:
        for lm in results.face_landmarks.landmark[::10]:  # every 10th point
            x, y = int(lm.x * width), int(lm.y * height)
            pygame.draw.circle(overlay, (*colors["face"], alpha), (x, y), 4)
    
    # Blit overlay on top of main screen
    screen.blit(overlay, (0, 0))


class Player:
    """Represents a player-controlled dot."""
    def __init__(self, color, start_pos):
        self.pos = pygame.Vector2(start_pos)
        self.color = color
        self.visible = True # Player is visible from the start

    def update_position(self, new_pos):
        if new_pos:
            target_x, target_y = new_pos
            
            # Clamp to safe zone if defined
            if 'SAFE_ZONE_RECT' in globals():
                target_x = max(SAFE_ZONE_RECT.left, min(SAFE_ZONE_RECT.right, target_x))
                target_y = max(SAFE_ZONE_RECT.top, min(SAFE_ZONE_RECT.bottom, target_y))
            
            target = pygame.Vector2(target_x, target_y)
            direction = target - self.pos
            distance = direction.length()
            
            # If too far, move gradually toward target
            if distance > PLAYER_MOVE_SPEED:
                direction = direction.normalize() * PLAYER_MOVE_SPEED
                self.pos += direction
            else:
                self.pos = target


    def draw(self, screen):
        if self.visible:
            pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), PLAYER_RADIUS)
            
    def get_rect(self):
        return pygame.Rect(self.pos.x - PLAYER_RADIUS, self.pos.y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)

class Bullet:
    """Represents a single bullet."""
    def __init__(self, pos, velocity):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)

    def update(self):
        self.pos += self.velocity

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.pos.x), int(self.pos.y)), BULLET_RADIUS)
        
    def is_offscreen(self):
        return not (0 < self.pos.x < WINDOW_WIDTH and 0 < self.pos.y < WINDOW_HEIGHT)

def main_menu(screen):
    """Displays the main menu and waits for user input."""
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 36)
    
    # --- FIX IS HERE ---
    # Store the original text strings, not the rendered surfaces
    option_texts = {
        1: "1: One Hand",
        2: "2: Two Hands",
        3: "3: Hands + Head"
    }
    
    title_surface = font.render("Select Tracking Mode", True, WHITE)
    instructions_surface = small_font.render("Press a number key to start", True, WHITE)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                selection = None
                if event.key == pygame.K_1: selection = 1
                if event.key == pygame.K_2: selection = 2
                if event.key == pygame.K_3: selection = 3
                
                if selection:
                    # Redraw the screen with the selected option highlighted in a different color
                    screen.fill(BLACK)
                    
                    # Render all options, changing the color for the selected one
                    for key, text in option_texts.items():
                        color = ORANGE if key == selection else WHITE
                        text_surface = font.render(text, True, color)
                        y_pos = 300 + (key - 1) * 100
                        screen.blit(text_surface, (WINDOW_WIDTH // 2 - text_surface.get_width() // 2, y_pos))

                    screen.blit(title_surface, (WINDOW_WIDTH // 2 - title_surface.get_width() // 2, 150))
                    screen.blit(instructions_surface, (WINDOW_WIDTH // 2 - instructions_surface.get_width() // 2, 650))
                    
                    pygame.display.flip()
                    pygame.time.wait(300) # Wait a moment so user sees the feedback
                    return selection

        # Default drawing loop
        screen.fill(BLACK)
        screen.blit(title_surface, (WINDOW_WIDTH // 2 - title_surface.get_width() // 2, 150))
        
        # Render all options with the default color
        for key, text in option_texts.items():
            text_surface = font.render(text, True, WHITE)
            y_pos = 300 + (key - 1) * 100
            screen.blit(text_surface, (WINDOW_WIDTH // 2 - text_surface.get_width() // 2, y_pos))
            
        screen.blit(instructions_surface, (WINDOW_WIDTH // 2 - instructions_surface.get_width() // 2, 650))
        pygame.display.flip()
        
    return None


def game_over_screen(screen, score):
    """Displays the game over message and final score."""
    font = pygame.font.Font(None, 100)
    small_font = pygame.font.Font(None, 50)
    
    title = font.render("GAME OVER", True, RED)
    score_text = small_font.render(f"Final Score: {score}", True, WHITE)
    restart_text = small_font.render("Press any key to return to menu", True, WHITE)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                return True
        
        screen.fill(BLACK)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 250))
        screen.blit(score_text, (WINDOW_WIDTH // 2 - score_text.get_width() // 2, 400))
        screen.blit(restart_text, (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 500))
        pygame.display.flip()

def draw_dotted_rect(screen, rect, color, dot_length=10, gap=5):
    # Top edge
    x = rect.left
    while x < rect.right:
        pygame.draw.line(screen, color, (x, rect.top), (min(x + dot_length, rect.right), rect.top))
        x += dot_length + gap
    # Bottom edge
    x = rect.left
    while x < rect.right:
        pygame.draw.line(screen, color, (x, rect.bottom), (min(x + dot_length, rect.right), rect.bottom))
        x += dot_length + gap
    # Left edge
    y = rect.top
    while y < rect.bottom:
        pygame.draw.line(screen, color, (rect.left, y), (rect.left, min(y + dot_length, rect.bottom)))
        y += dot_length + gap
    # Right edge
    y = rect.top
    while y < rect.bottom:
        pygame.draw.line(screen, color, (rect.right, y), (rect.right, min(y + dot_length, rect.bottom)))
        y += dot_length + gap

def game_loop(screen, tracking_mode):
    """The main loop for tracking and the game itself."""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)
    
    # --- Game State ---
    players = []
    if tracking_mode == 1:
        players.append(Player(GREEN, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50)))
    elif tracking_mode == 2:
        players.append(Player(GREEN, (WINDOW_WIDTH * 0.75, WINDOW_HEIGHT - 50)))
        players.append(Player(BLUE, (WINDOW_WIDTH * 0.25, WINDOW_HEIGHT - 50)))
    elif tracking_mode == 3:
        players.append(Player(GREEN, (WINDOW_WIDTH * 0.75, WINDOW_HEIGHT - 50)))
        players.append(Player(BLUE, (WINDOW_WIDTH * 0.25, WINDOW_HEIGHT - 50)))
        players.append(Player(RED, (WINDOW_WIDTH // 2, 100)))

    bullets = []
    last_spawn_time = time.time()
    start_time = time.time()
    score = 0
    game_over = False
    
    # -- New Dynamic Variables --
    current_spawn_rate = INITIAL_BULLET_SPAWN_RATE
    current_bullet_speed = BULLET_SPEED
    ring_rotation_angle = 0
    
    font = pygame.font.Font(None, 50)
    countdown_font = pygame.font.Font(None, 150)
    
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        running = True
        while running and cap.isOpened() and not game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False

            success, frame = cap.read()
            if not success: continue

            frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            frame.flags.writeable = False
            results = holistic.process(frame)
            frame.flags.writeable = True
            
            # Convert frame for pygame display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
            
            # Resize frame to match window if needed
            if frame_rgb.shape[:2] != (WINDOW_HEIGHT, WINDOW_WIDTH):
                frame_rgb = cv2.resize(frame_rgb, (WINDOW_WIDTH, WINDOW_HEIGHT))
            
            # Convert to pygame surface
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            
            frame_height, frame_width, _ = frame.shape
            
            # --- Update Player Positions ---
            if tracking_mode == 1:
                pos = calculate_centroid(results.right_hand_landmarks or results.left_hand_landmarks, (frame_height, frame_width), is_hand=True)
                players[0].update_position(pos)
            elif tracking_mode == 2:
                players[0].update_position(calculate_centroid(results.right_hand_landmarks, (frame_height, frame_width), is_hand=True))
                players[1].update_position(calculate_centroid(results.left_hand_landmarks, (frame_height, frame_width), is_hand=True))
            elif tracking_mode == 3:
                players[0].update_position(calculate_centroid(results.right_hand_landmarks, (frame_height, frame_width), is_hand=True))
                players[1].update_position(calculate_centroid(results.left_hand_landmarks, (frame_height, frame_width), is_hand=True))
                players[2].update_position(calculate_centroid(results.face_landmarks, (frame_height, frame_width)))

            
            # --- Game Logic ---
            current_time = time.time()
            time_since_start = current_time - start_time

            # Only run game logic after the grace period
            if time_since_start > GRACE_PERIOD:
                # Spawn bullets
                if current_time - last_spawn_time > current_spawn_rate:
                    last_spawn_time = current_time
                    ring_rotation_angle += random.randint(5, 45)
                    emitter_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                    bullets_per_ring = BULLETS_PER_RING + random.randint(-4, 4)
                    bullet_speed = current_bullet_speed + random.uniform(-2, 2)
                    for i in range(bullets_per_ring):
                        angle = (360 / bullets_per_ring) * i + ring_rotation_angle
                        rad_angle = math.radians(angle)
                        velocity = (math.cos(rad_angle) * bullet_speed, math.sin(rad_angle) * bullet_speed)
                        bullets.append(Bullet(emitter_pos, velocity))
                    
                    # Increase difficulty
                    current_spawn_rate = max(MINIMUM_SPAWN_RATE, current_spawn_rate * SPAWN_RATE_ACCELERATION)
                    current_bullet_speed = min(MAXIMUM_BULLET_SPEED, current_bullet_speed * BULLET_SPEED_ACCELERATION)

                # Update score
                score = int(time_since_start - GRACE_PERIOD)

            # Update bullets (always, so they fly away during grace period if any exist)
            for bullet in bullets[:]:
                bullet.update()
                if bullet.is_offscreen():
                    bullets.remove(bullet)
            
            # Check for collisions
            for player in players:
                player_rect = player.get_rect()
                for bullet in bullets:
                    if player_rect.collidepoint(bullet.pos):
                        game_over = True
                        break
                if game_over: break

            # --- Drawing ---
            # Use camera feed as background
            screen.blit(frame_surface, (0, 0))
            
            # Draw semi-transparent overlay for better visibility
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(200)  # Adjust transparency (0-255)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            for player in players: player.draw(screen)
            for bullet in bullets: bullet.draw(screen)

            # Draw safe zone
            draw_dotted_rect(screen, SAFE_ZONE_RECT, (255, 255, 255))  # white dotted border
            
            # Draw hand landmarks
            hand_colors = {"left": BLUE, "right": GREEN}
            draw_hand_landmarks(screen, results, (frame_height, frame_width), hand_colors)

            # Draw score or countdown
            if time_since_start > GRACE_PERIOD:
                score_surface = font.render(f"Score: {score}", True, WHITE)
                screen.blit(score_surface, (10, 10))
                
                # Display bullet spawn rate and speed
                bullets_per_second = 1.0 / current_spawn_rate
                speed_text = f"Rings/s: {bullets_per_second:.1f} | Speed: {current_bullet_speed:.0f}"
                speed_surface = font.render(speed_text, True, WHITE)
                screen.blit(speed_surface, (WINDOW_WIDTH // 2 - speed_surface.get_width() // 2, WINDOW_HEIGHT - 50))
            else:
                countdown = GRACE_PERIOD - int(time_since_start) + 1
                countdown_text = countdown_font.render(str(countdown), True, WHITE)
                screen.blit(countdown_text, (WINDOW_WIDTH // 2 - countdown_text.get_width() // 2, WINDOW_HEIGHT // 2 - countdown_text.get_height() // 2))

            pygame.display.flip()
            # Remove OpenCV window display
            if cv2.waitKey(5) & 0xFF == 27: running = False
                
    cap.release()
    cv2.destroyAllWindows()
    return score, game_over

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Bullet Hell Game")

    app_running = True
    while app_running:
        mode = main_menu(screen)
        if mode is not None:
            final_score, was_game_over = game_loop(screen, mode)
            if was_game_over:
                app_running = game_over_screen(screen, final_score)
        else:
            app_running = False

    pygame.quit()
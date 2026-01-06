import pygame
import cv2
import mediapipe as mp
import numpy as np
import time
import random
from datetime import datetime

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Alphattack - Hand Semaphore Version")
clock = pygame.time.Clock()

# --- Import assets and UI components ---
from assets.assets import BLACK, WHITE, GREEN, BLUE, font, big_font
from game.UI.status_section import StatusPanel, GAMEOVER_EVENT
from game.UI.semaphore_detected_section import SEMAPHORE_COMPLETE_EVENT, SemaphorePanel
from game.UI.bonus_bar_section import BONUSBAR_FULL_EVENT, BonusBar
from game.UI.webcam_section import WebcamPanel, cap
from game.gameplay_section import Gameplay
from game.logger import GameplayLogger
from game.logger import WebcamLogger

# Initialize loggers
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
gameplay_logger = GameplayLogger(f"logs/gameplay_logs_{timestamp}.jsonl")
webcam_logger = WebcamLogger(f"logs/webcam_logs_{timestamp}.jsonl")

# --- Layout computation ---
game_col_width = SCREEN_HEIGHT  # Square gameplay area
ui_col_width = SCREEN_WIDTH - game_col_width

# Row heights
row4_height = SCREEN_HEIGHT // 2
row3_height = 20
remaining_height = SCREEN_HEIGHT - (row4_height + row3_height)
row1_height = remaining_height // 2
row2_height = remaining_height - row1_height

# --- Instantiate panels ---
gameplay_section = Gameplay(pygame.Rect(0, 0, game_col_width, SCREEN_HEIGHT), gameplay_logger)
status_section = StatusPanel(pygame.Rect(game_col_width, 0, ui_col_width, row1_height), gameplay_logger)
semaphore_section = SemaphorePanel(pygame.Rect(game_col_width, row1_height, ui_col_width, row2_height))
bonus_section = BonusBar(pygame.Rect(game_col_width, row1_height + row2_height, ui_col_width, row3_height))
webcam_section = WebcamPanel(pygame.Rect(game_col_width, row1_height + row2_height + row3_height, ui_col_width, row4_height), webcam_logger)

# Cross-references
gameplay_section.status_panel = status_section
gameplay_section.bonus_bar = bonus_section
gameplay_section.semaphore_panel = semaphore_section

# --- Debug mode ---
debug_mode = False

# --- Main loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # print("Quitting game...")   # currently it just freezes and you have to force quit with ctlr+c, idk why
            # cap.release()
            # pygame.quit()
            # exit()
            running = False

        elif event.type == GAMEOVER_EVENT:
            gameplay_section.gameover()

        elif event.type == SEMAPHORE_COMPLETE_EVENT:
            gameplay_section.semaphore_input(event.semaphore)

        elif event.type == BONUSBAR_FULL_EVENT:
            gameplay_section.bonus_bar_filled()

        elif event.type == pygame.USEREVENT + 10:  # resolve bonus missile
            gameplay_section.resolve_bonus_event()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                debug_mode = not debug_mode
                print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")

    frame, detected_semaphore = webcam_section.update()
    new_semaphore = detected_semaphore
    
    # Update dependent panels
    semaphore_section.update_semaphore_detected(new_semaphore)
    bonus_section.update_semaphore_detected(new_semaphore)

    semaphore_section.update()
    bonus_section.update()
    # frame = webcam_section.update()
    gameplay_section.update()

    screen.fill(BLACK)
    gameplay_section.draw(screen, debug_mode=debug_mode)
    status_section.draw(screen)
    semaphore_section.draw(screen)
    bonus_section.draw(screen)
    webcam_section.draw(screen, frame, debug_mode=debug_mode)

    pygame.display.flip()
    clock.tick(60)

# cap.release()
# pygame.quit()
print("Initiating shutdown...")
webcam_section.close()  # Close MediaPipe first
cap.release()           # Release the Camera
cv2.destroyAllWindows() # Close any hidden CV2 windows
pygame.quit()           # Close Pygame
print("Shutdown complete.")
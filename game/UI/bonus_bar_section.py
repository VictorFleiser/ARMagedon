import pygame
import cv2
import mediapipe as mp
import numpy as np
import time

from assets.assets import GREEN, GRAY

# Custom Pygame event type for when the bar is full
BONUSBAR_FULL_EVENT = pygame.USEREVENT + 3

class BonusBar:
    def __init__(self, rect):
        self.rect = rect

# --- Configuration ---
        # --- State ---
        self.base_score_for_full = 3000  # score needed to fill the bar by default
        self.level_increment = 100  # additional score needed per level
        self.score_for_full = self.base_score_for_full  # score needed to fill the bar currently
        self.current_score = 0 # Current score in the bar
        self.progress = self.current_score / self.score_for_full    # progress of the bar
        self.displayed_progress = self.progress  # actual progress displayed on the bar (for smooth animation)

        # --- Style ---
        self.color_bg = GRAY
        self.color_fill = GREEN

    def gain_score(self, amount):
        self.current_score += amount
        self.progress = self.current_score / self.score_for_full

    def update(self):
        # Smooth animation of displayed progress, approach the actual progress by lerping
        lerp_speed = 0.3
        self.displayed_progress += (self.progress - self.displayed_progress) * lerp_speed
        
        # Check completion (when the displayed progress is full, not the actual progress):
        if self.displayed_progress >= 1.0:
            self.filled_bar()

    def filled_bar(self):
        # Emit event
        event = pygame.event.Event(BONUSBAR_FULL_EVENT)
        pygame.event.post(event)
        # Reset
        self.current_score -= self.score_for_full
        self.score_for_full += self.level_increment
        self.progress = self.current_score / self.score_for_full
        self.displayed_progress = 0.0

    def draw(self, surface):
        pygame.draw.rect(surface, self.color_bg, self.rect)
        fill_width = int(self.rect.width * self.displayed_progress)
        pygame.draw.rect(
            surface, self.color_fill,
            (self.rect.x, self.rect.y, fill_width, self.rect.height)
        )
    
    def reset_increment(self):
        # Reset score needed for full bar to base value after missile reaches bottom
        self.score_for_full = self.base_score_for_full
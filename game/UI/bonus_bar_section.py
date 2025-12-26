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
        self.time_to_complete_fast = 10.0   # seconds to fill in fast mode
        self.time_to_complete_slow = 30.0  # seconds to fill in slow mode

        # --- State ---
        self.progress = 0.0
        self.fast_increase = False
        self.last_update_time = time.time()

        # --- Style ---
        self.color_bg = GRAY
        self.color_fill = GREEN

    def update_semaphore_detected(self, new_semaphore_detected):
        """Adjusts speed mode based on detected semaphore."""
        self.fast_increase = (new_semaphore_detected == "NONE")

    def update(self):
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        self.last_update_time = current_time

        # Determine rate based on mode
        duration = (
            self.time_to_complete_fast if self.fast_increase
            else self.time_to_complete_slow
        )

        # Increase progress based on time fraction
        if duration > 0:
            self.progress += elapsed / duration

        # Clamp and check completion
        if self.progress >= 1.0:
            self.progress = 1.0
            # Emit event
            event = pygame.event.Event(BONUSBAR_FULL_EVENT)
            pygame.event.post(event)
            # Reset
            self.progress = 0.0

    def draw(self, surface):
        pygame.draw.rect(surface, self.color_bg, self.rect)
        fill_width = int(self.rect.width * self.progress)
        pygame.draw.rect(
            surface, self.color_fill,
            (self.rect.x, self.rect.y, fill_width, self.rect.height)
        )
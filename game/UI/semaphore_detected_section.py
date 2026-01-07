import pygame
import cv2
import mediapipe as mp
import numpy as np
import time
import math

from assets.assets import WHITE, GREEN, GRAY, PURPLE, big_font, semaphore_images

# Custom event type for progress completion
SEMAPHORE_COMPLETE_EVENT = pygame.USEREVENT + 1

class SemaphorePanel:
    def __init__(self, rect):
        self.rect = rect

        self.semaphore_detected = "NONE"

        # Progress management
        self.progress = 0.0
        self.last_update_time = time.time()
        self.completed = False

        # Timing (0.5 seconds to full progress)
        self.progress_duration = 0.5

    def update_semaphore_detected(self, new_semaphore_detected):
        """Called by main when a new semaphore letter is detected."""
        if new_semaphore_detected != self.semaphore_detected:
            self.semaphore_detected = new_semaphore_detected
            # Reset progress if signal changes
            self.progress = 0.0
            self.completed = False
            self.last_update_time = time.time()

    def update(self):
        """Updates progress based on time and semaphore state."""
        current_time = time.time()

        # Only progress if a valid letter or BOMB is detected and not completed
        # if not self.completed and (
        #     (self.semaphore_detected.isalpha() and len(self.semaphore_detected) == 1)
        #     or self.semaphore_detected == "BOMB"
        # ):
        if not self.completed :
            elapsed = current_time - self.last_update_time
            self.progress = min(elapsed / self.progress_duration, 1.0)
            if self.progress >= 1.0:
                self.completed = True
                # Send a Pygame event to main
                event = pygame.event.Event(SEMAPHORE_COMPLETE_EVENT, {
                    "semaphore": self.semaphore_detected
                })
                pygame.event.post(event)
        else:
            # Otherwise, stay empty
            if not self.completed:
                self.progress = 0.0

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, self.rect)
        x, y, w, h = self.rect

        # --- Left: semaphore image with purple outline ---
        img_area_w = w // 3
        img_area_h = h - 20
        img_x = x + 10
        img_y = y + 10

        # Get correct image
        img = semaphore_images.get(self.semaphore_detected)
        if img is None:
            img = pygame.Surface((img_area_h, img_area_h))
            img.fill((100, 100, 100))
        
        # Scale image to fit area (keeping aspect ratio)
        scale = min(img_area_w / img.get_width(), img_area_h / img.get_height())
        new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
        scaled_img = pygame.transform.smoothscale(img, new_size)

        # Draw outline
        outline_rect = pygame.Rect(
            img_x - 3, img_y - 3,
            scaled_img.get_width() + 6,
            scaled_img.get_height() + 6
        )
        pygame.draw.rect(surface, (255, 255, 255), outline_rect, border_radius=8)
        pygame.draw.rect(surface, PURPLE, outline_rect, border_radius=8, width=3)
        surface.blit(scaled_img, (img_x, img_y))

        # --- Middle: arrow ---
        mid_x = x + w // 2
        mid_y = y + h // 2
        pygame.draw.polygon(surface, WHITE, [
            (mid_x - 20, mid_y - 10),
            (mid_x + 20, mid_y),
            (mid_x - 20, mid_y + 10)
        ])

        # --- Right: letter and circular progress ---
        letter_area_x = x + (2 * w // 3)
        letter_area_center = (letter_area_x + w // 6, y + h // 2)

        # Determine letter to display
        if self.semaphore_detected.isalpha() and len(self.semaphore_detected) == 1:
            display_symbol = self.semaphore_detected.upper()
        elif self.semaphore_detected == "BOMB":
            display_symbol = "☆"
        else:
            display_symbol = "-"

        letter_surface = big_font.render(display_symbol, True, WHITE)
        letter_rect = letter_surface.get_rect(center=letter_area_center)
        surface.blit(letter_surface, letter_rect)

        # Draw progress circle (clockwise from top)
        radius = 80
        center = letter_rect.center
        start_angle = math.pi / 2  # start at top
        end_angle = start_angle - (2 * math.pi * self.progress)  # clockwise

        # Draw base circle
        pygame.draw.circle(surface, WHITE, center, radius, 3)

        if self.progress > 0:
            pygame.draw.arc(
                surface,
                PURPLE,
                (center[0] - radius, center[1] - radius, radius * 2, radius * 2),
                end_angle,
                start_angle,
                8
            )

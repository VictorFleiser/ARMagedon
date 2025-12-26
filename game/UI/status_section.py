import pygame
import cv2
import mediapipe as mp
import numpy as np
import time

from assets.assets import GRAY, WHITE, PINK, BLUE, PURPLE, font, semaphore_images, life_images, bomb_images

GAMEOVER_EVENT = pygame.USEREVENT + 2

# --- Helper: get scaled image ---
def get_scaled(img, line_height):
    """Scale image to fit the line height (keeping aspect ratio)."""
    h = line_height - 4  # slight margin
    w = int(img.get_width() * (h / img.get_height()))
    return pygame.transform.smoothscale(img, (w, h))

class StatusPanel:
    def __init__(self, rect, gameplay_logger):
        self.rect = rect
        self.gameplay_logger = gameplay_logger

        self.score = 0

        self.lives = 3
        self.life_fragments = 0
        self.life_slots = 8

        self.bombs = 3
        self.bomb_fragments = 0
        self.bomb_slots = 8

        # --- scale images to fit line height ---
        self.line_height = 45
        self.margin_left = 10
        self.spacing = 5

        for i in range(len(life_images)):
            life_images[i] = get_scaled(life_images[i], self.line_height)
        for i in range(len(bomb_images)):
            bomb_images[i] = get_scaled(bomb_images[i], self.line_height)

    def take_damage(self):
        """Removes one full life if available."""
        self.lives -= 1
        # logging
        self.gameplay_logger.lives_updated(self.lives, self.life_fragments)
        if self.lives <= 0:
            pygame.event.post(pygame.event.Event(GAMEOVER_EVENT))

    def gain_life_fragments(self, number):
        """Adds fragments; converts to full lives when possible."""
        self.life_fragments += number
        while self.life_fragments >= 4 :
            self.life_fragments -= 4
            self.lives += 1
        # make sure we don't exceed max lives
        self.lives = min(self.lives, self.life_slots)
        if self.lives == self.life_slots:
            self.life_fragments = 0  # can't store fragments if at max lives
        # logging
        self.gameplay_logger.lives_updated(self.lives, self.life_fragments)
        
    def use_bomb(self, number=1):
        """Consumes bombs if available.
        The number of bombs to use can be specified (for instance if we implement death-bombs consuming up to 2 bombs to cancel death mid animation).
        Returns True if at least one bomb is used, False otherwise.
        """
        sucess = False
        if self.bombs >= 1:
            sucess = True
            self.bombs -= number
        self.bombs = max(self.bombs, 0)
        # logging
        self.gameplay_logger.bombs_updated(self.bombs, self.bomb_fragments)
        return sucess

    def gain_bomb_fragments(self, number):
        """Adds fragments; converts to full bombs when possible."""
        self.bomb_fragments += number
        while self.bomb_fragments >= 4 :
            self.bomb_fragments -= 4
            self.bombs += 1
        # make sure we don't exceed max bombs
        self.bombs = min(self.bombs, self.bomb_slots)
        if self.bombs == self.bomb_slots:
            self.bomb_fragments = 0  # can't store fragments if at max bombs
        # logging
        self.gameplay_logger.bombs_updated(self.bombs, self.bomb_fragments)

    def gain_score(self, number):
        self.score += number
        # logging
        self.gameplay_logger.score_updated(self.score)

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, self.rect)
        x, y = self.rect.topleft

        # --- 1. Score (white) ---
        score_y = y + self.spacing
        score_text = font.render(f"Score : {self.score:06d}", True, WHITE)
        surface.blit(score_text, (x + self.margin_left, score_y))

        # --- 2. Lives (pink + icons) ---
        lives_y = score_y + self.line_height + self.spacing
        lives_text = font.render("Lives :", True, PINK)
        surface.blit(lives_text, (x + self.margin_left, lives_y))

        # Draw 8 life slots
        icon_x = x + 120
        current_total = self.lives * 4 + self.life_fragments
        for i in range(self.life_slots):
            # Determine which image to use for this slot
            # Each life = 4 fragments (4 full = one full icon)
            remaining_fragments = current_total - (i * 4)
            if remaining_fragments >= 4:
                img = life_images[4]
            elif remaining_fragments > 0:
                img = life_images[remaining_fragments]
            else:
                img = life_images[0]

            surface.blit(img, (icon_x + i * (img.get_width() + self.spacing), lives_y))

        # --- 3. Bombs (blue + icons + semaphore image) ---
        bombs_y = lives_y + self.line_height + self.spacing
        bombs_text = font.render("Bombs :", True, BLUE)
        surface.blit(bombs_text, (x + self.margin_left, bombs_y))

        icon_x = x + 120
        current_total = self.bombs * 4 + self.bomb_fragments
        for i in range(self.bomb_slots):
            remaining_fragments = current_total - (i * 4)
            if remaining_fragments >= 4:
                img = bomb_images[4]
            elif remaining_fragments > 0:
                img = bomb_images[remaining_fragments]
            else:
                img = bomb_images[0]
            surface.blit(img, (icon_x + i * (img.get_width() + self.spacing), bombs_y))

        # Semaphore hint image at end of bombs row
        sema_x = icon_x + self.bomb_slots * (bomb_images[0].get_width() + self.spacing) + self.margin_left
        sema_y = bombs_y - 5
        scaled_img = get_scaled(semaphore_images["SPACE"], self.line_height)

        # Draw outline
        outline_rect = pygame.Rect(
            sema_x - 3, sema_y - 3,
            scaled_img.get_width() + 6,
            scaled_img.get_height() + 6
        )
        pygame.draw.rect(surface, WHITE, outline_rect, border_radius=8)
        pygame.draw.rect(surface, PURPLE, outline_rect, border_radius=8, width=3)

        # Draw the semaphore image
        surface.blit(scaled_img, (sema_x, sema_y))

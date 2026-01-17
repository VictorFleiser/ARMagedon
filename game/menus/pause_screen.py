# pause screen : semi-transparent overlay with "Paused" text and resume/quit buttons
import pygame
from game.game_clock import GameClock

class PauseScreen:
    def __init__(self, screen_rect, game_clock: GameClock):
        self.screen_rect = screen_rect
        self.game_clock = game_clock
        self.font = pygame.font.SysFont(None, 72)
        self.small_font = pygame.font.SysFont(None, 36)
        self.overlay = pygame.Surface((screen_rect.width, screen_rect.height))
        self.overlay.set_alpha(128)  # semi-transparent
        self.overlay.fill((0, 0, 0))  # black overlay

        # Buttons
        self.resume_button_rect = pygame.Rect(0, 0, 200, 50)
        self.resume_button_rect.center = (screen_rect.centerx, screen_rect.centery - 40)
        self.quit_button_rect = pygame.Rect(0, 0, 200, 50)
        self.quit_button_rect.center = (screen_rect.centerx, screen_rect.centery + 40)

    def draw(self, surface):
        # Draw overlay
        surface.blit(self.overlay, (0, 0))

        # Draw "Paused" text
        paused_text = self.font.render("Paused", True, (255, 255, 255))
        paused_rect = paused_text.get_rect(center=(self.screen_rect.centerx, self.screen_rect.centery - 100))
        surface.blit(paused_text, paused_rect)

        # Draw buttons
        pygame.draw.rect(surface, (100, 100, 100), self.resume_button_rect)
        resume_text = self.small_font.render("Resume", True, (255, 255, 255))
        resume_rect = resume_text.get_rect(center=self.resume_button_rect.center)
        surface.blit(resume_text, resume_rect)

        pygame.draw.rect(surface, (100, 100, 100), self.quit_button_rect)
        quit_text = self.small_font.render("Quit", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=self.quit_button_rect.center)
        surface.blit(quit_text, quit_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.resume_button_rect.collidepoint(event.pos):
                self.game_clock.resume("player_resumed")
            elif self.quit_button_rect.collidepoint(event.pos):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
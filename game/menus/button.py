# game/ui/button.py
import pygame

class Button:
    def __init__(self, rect, text, font, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface):
        pygame.draw.rect(surface, (80, 80, 80), self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)

        txt = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(
            txt,
            txt.get_rect(center=self.rect.center)
        )
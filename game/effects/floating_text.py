# game/effects/floating_text.py
from game.effects.base_effect import Effect

class FloatingTextEffect(Effect):
    def __init__(self, pos, text, font, color):
        super().__init__(duration=2.0)
        self.x, self.y = pos
        self.text = text
        self.font = font
        self.color = color

    def update(self, dt):
        super().update(dt)
        self.y -= 30 * dt  # slide up

    def draw(self, surface):
        surf = self.font.render(self.text, True, self.color)
        rect = surf.get_rect(center=(self.x, self.y))
        surface.blit(surf, rect)

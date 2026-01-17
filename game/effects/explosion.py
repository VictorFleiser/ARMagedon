# game/effects/explosion.py
import pygame
from game.effects.base_effect import Effect

class ExplosionEffect(Effect):
    def __init__(self, pos, sprite):
        super().__init__(duration=0.5)
        self.original_sprite = sprite
        self.pos = pos
        self.rotation = 0
        self.rotation_speed = 720 # 2 rot/s
        self.initial_scale = 1.5
        self.final_scale = 4.0

    def update(self, dt):
        super().update(dt)
        self.rotation += self.rotation_speed * dt

    def draw(self, surface):
        progress = min(1.0, self.elapsed / self.duration)
        scale = self.initial_scale + (self.final_scale - self.initial_scale) * progress
        alpha = int(255 * (1.0 - progress))
        w, h = self.original_sprite.get_size()
        size = (int(w * scale), int(h * scale))
        scaled_sprite = pygame.transform.scale(self.original_sprite, size)
        rotated_sprite = pygame.transform.rotate(scaled_sprite, self.rotation)
        rotated_sprite.set_alpha(alpha)
        
        rect = rotated_sprite.get_rect(center=self.pos)
        surface.blit(rotated_sprite, rect)
# game/effects/explosion.py
import pygame
from game.effects.base_effect import Effect

class ExplosionEffect(Effect):
    def __init__(self, pos, sprite):
        super().__init__(duration=0.4)
        self.sprite = sprite
        self.pos = pos

    def draw(self, surface):
        rect = self.sprite.get_rect(center=self.pos)
        surface.blit(self.sprite, rect)

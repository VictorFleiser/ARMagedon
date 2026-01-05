# game/missile.py
import pygame
import uuid

from assets.assets import PURPLE
from assets.assets import SEMAPHORES_PATH


sprite = pygame.image.load("assets/sprites/missile.png").convert_alpha()
hint_sprites = [pygame.image.load(f"{SEMAPHORES_PATH}{chr(ord('A') + i)}.png").convert_alpha() for i in range(26)]
hint_sprites = [pygame.transform.scale(img, (100, 100)) for img in hint_sprites]

class Missile:

	def __init__(
		self,
		column,
		letter,
		speed,
		hint_start,
		grid_size,
		gameplay_rect,
		font,
		gameplay
	):
		self.id = uuid.uuid4()

		self.column = column
		self.letter = letter
		self.speed_time = speed
		self.hint_start = hint_start

		self.gameplay_rect = gameplay_rect
		self.grid_size = grid_size

		self.sprite = sprite
		self.hint_sprite = hint_sprites[ord(letter) - ord('A')]
		self.font = font

		self.gameplay = gameplay

		# --- Geometry ---
		self.cell_width = gameplay_rect.width / grid_size

		self.x = gameplay_rect.left + (column + 0.5) * self.cell_width
		self.y = gameplay_rect.top - self.sprite.get_height() / 2

		self.start_y = self.y
		self.end_y = gameplay_rect.bottom + self.sprite.get_height() / 2
		self.distance = self.end_y - self.start_y

		self.velocity = self.distance / self.speed_time  # pixels per second

		self.alive = True

		self.shown_hint_flag = False	# to track when to send the missile_hint_shown log

	# -------------------------------------------------------
	def update(self, dt):
		if not self.alive:
			return

		self.y += self.velocity * dt

		if self.y >= self.end_y:
			self.alive = False
			self.on_reach_bottom()
			return True  # Indicate that the missile has reached the bottom
		return False

	def on_reach_bottom(self):
		self.gameplay.take_damage()
		
		# logging
		self.gameplay.gameplay_logger.missile_hit_ground(self, (self.y - self.start_y) / self.distance)



	# -------------------------------------------------------
	def should_show_hint(self):
		progress = (self.y - self.start_y) / self.distance
		return progress >= self.hint_start

	# -------------------------------------------------------
	def draw(self, surface):
		if not self.alive:
			return

		# Missile sprite
		rect = self.sprite.get_rect(center=(self.x, self.y))
		surface.blit(self.sprite, rect)

		# Letter overlay
		letter_surface = self.font.render(self.letter, True, (0, 0, 0))
		letter_rect = letter_surface.get_rect(center=(self.x, self.y))
		surface.blit(letter_surface, letter_rect)

		# Hint sprite (above missile)
		if self.should_show_hint():
			if not self.shown_hint_flag:
				# logging
				self.gameplay.gameplay_logger.missile_hint_shown(self)
				self.shown_hint_flag = True
				
				# Update BKT with incorrect when hint is shown
				if hasattr(self.gameplay, 'spawner'):
					if hasattr(self.gameplay.spawner, 'on_missile_hint_shown'):
						self.gameplay.spawner.on_missile_hint_shown(self.letter)

			hint_rect = self.hint_sprite.get_rect(
				center=(self.x, self.y - self.sprite.get_height() // 2 - self.hint_sprite.get_height() // 2 - 10)
			)
			# Draw outline and background
			outline_rect = pygame.Rect(
				hint_rect.x - 3, hint_rect.y - 3,
				self.hint_sprite.get_width() + 6,
				self.hint_sprite.get_height() + 6
			)
			pygame.draw.rect(surface, (255, 255, 255), outline_rect, border_radius=8)
			pygame.draw.rect(surface, PURPLE, outline_rect, border_radius=8, width=3)
			surface.blit(self.hint_sprite, hint_rect)
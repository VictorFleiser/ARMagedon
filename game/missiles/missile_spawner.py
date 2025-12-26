import random

from game.missiles.missile import Missile

class MissileSpawner:
	def __init__(self, gameplay):
		self.gameplay = gameplay

	def update(self, dt):
		"""Called every frame"""
		pass
	
	def get_free_column(self):
		# Return a free column index, tries avoiding adjacent occupied columns to reduce overlap between hints sprites, if no free column found return None
		grid_size = self.gameplay.grid_size

		occupied = self.gameplay.get_occupied_columns()

		# --- Compute column candidates
		all_columns = set(range(grid_size))
		free_columns = all_columns - occupied

		if not free_columns:
			return None

		# First pass: free & non-adjacent
		safe_columns = []
		for c in free_columns:
			if (c - 1 not in occupied) and (c + 1 not in occupied):
				safe_columns.append(c)

		if safe_columns:
			candidate_columns = safe_columns
		else:
			candidate_columns = list(free_columns)
		
		column = random.choice(candidate_columns)
		return column
	
	def get_free_letters(self):
		# Return all letters that are not currently active in any missile
		all_letters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
		active_letters = self.gameplay.get_active_letters()

		free_letters = list(all_letters - active_letters)

		if not free_letters:
			return None
		
		return free_letters
	
	def spawn_missile(self, column, letter, speed, hint_start):
		missile = Missile(
			column=column,
			letter=letter,
			speed=speed,
			hint_start=hint_start,
			grid_size=self.gameplay.grid_size,
			gameplay_rect=self.gameplay.rect,
			font=self.gameplay.missile_font,
			gameplay=self.gameplay
		)
		self.gameplay.missiles.append(missile)
		# logging
		self.gameplay.gameplay_logger.missile_spawned(missile)
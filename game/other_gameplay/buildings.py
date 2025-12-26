# game/buildings.py
import pygame

class BuildingGrid:
	def __init__(self, grid_size, gameplay_rect, source_folder):
		self.grid_size = grid_size
		self.rect = gameplay_rect

		self.cell_width = gameplay_rect.width / grid_size
		self.cell_height = gameplay_rect.height / grid_size

		self.grid = [
			[0 for _ in range(grid_size)]
			for _ in range(grid_size)
		]

		self.sprites = {}  # (col, row, state) -> sprite

		self.load_sprites(source_folder)
		# pattern in source_folder/pattern.txt
		# each line: col row state
		pattern_path = f"{source_folder}/pattern.txt"
		try:
			with open(pattern_path, "r") as f:
				for line in f:
					parts = line.strip().split()
					if len(parts) != 3:
						continue
					col, row, state = map(int, parts)
					if 0 <= col < grid_size and 0 <= row < grid_size:
						self.grid[row][col] = state
		except FileNotFoundError:
			pass

	# ------------------------------------------------
	def load_sprites(self, folder):
		for col in range(self.grid_size):
			for row in range(self.grid_size):
				for state in (1, 2):
					path = f"{folder}/{col:02d}_{row:02d}_{state}.png"
					try:
						self.sprites[(col, row, state)] = pygame.image.load(path).convert_alpha()
						# resize sprite to cell size
						self.sprites[(col, row, state)] = pygame.transform.scale(
							self.sprites[(col, row, state)],
							(int(self.cell_width), int(self.cell_height))
						)
					except FileNotFoundError:
						pass

	def draw(self, surface):
		for row in range(self.grid_size):
			for col in range(self.grid_size):
				status = self.grid[row][col]
				if status == 0:
					continue

				sprite = self.sprites.get((col, row, status))
				if not sprite:
					continue

				x = self.rect.left + col * self.cell_width
				y = self.rect.bottom - (row + 1) * self.cell_height

				surface.blit(sprite, (x, y))

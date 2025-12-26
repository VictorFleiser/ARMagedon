import os
import pygame
pygame.init()
from PIL import Image

# THIS CODE IS NOT USED IN THE GAME, IT IS ONLY A TOOL TO CREATE BUILDING PATTERNS
# it takes an image, a grid size, a building grid, and generates the sprites and pattern file

INPUT_IMAGE_PATH = "assets/building_patterns/building_pattern_2/city.png"
OUTPUT_FOLDER = "assets/building_patterns/building_pattern_2"
GRID_SIZE = 10  # 10x10 grid
GRID = [
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
	[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
	[1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]
DESTRUCTION_MASK_IMG_PATH = "assets/building_patterns/destruction_mask.png"

# Load input image
input_image = Image.open(INPUT_IMAGE_PATH)
img_width, img_height = input_image.size
# if not square, increase height to match width, then move image to bottom
if img_height < img_width:
	new_image = Image.new("RGBA", (img_width, img_width), (0, 0, 0, 0))
	new_image.paste(input_image, (0, img_width - img_height))
	input_image = new_image
	img_height = img_width
cell_width = img_width // GRID_SIZE

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Generate sprites and pattern file
pattern_lines = []
for row in range(GRID_SIZE):
	for col in range(GRID_SIZE):
		status = GRID[row][col]
		if status == 0:
			continue  # no building, skip

		# Crop the cell image
		left = col * cell_width
		top = row * cell_width
		right = left + cell_width
		bottom = top + cell_width
		cell_image = input_image.crop((left, top, right, bottom))

		# Save sprites for each state
		game_row_index = GRID_SIZE - 1 - row  # invert row for saving
		for state in (1, 2):
			sprite_path = os.path.join(OUTPUT_FOLDER, f"{col:02d}_{game_row_index:02d}_{state}.png")
			if state == 2:
				cell_image.save(sprite_path)
			else:
				# Create damaged version : apply destruction mask to image
				destruction_mask = Image.open(DESTRUCTION_MASK_IMG_PATH).resize((cell_width, cell_width)).convert("L")
				damaged_image = cell_image.copy()
				damaged_image.putalpha(destruction_mask)
				damaged_image.save(sprite_path)
				# damaged_image = cell_image.point(lambda p: p * 0.5)
				# damaged_image.save(sprite_path)

		# Add to pattern file
		pattern_lines.append(f"{col} {game_row_index} 2")

# Write pattern file
pattern_path = os.path.join(OUTPUT_FOLDER, "pattern.txt")
with open(pattern_path, "w") as f:
	for line in pattern_lines:
		f.write(line + "\n")
print(f"Building pattern sprites and pattern file generated in '{OUTPUT_FOLDER}'")
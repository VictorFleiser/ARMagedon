
import os
import random

# Step 0 : create output directory if not exists
OG_semaphore_dir = "assets/semaphores"
if not os.path.exists(OG_semaphore_dir):
	raise FileNotFoundError(f"Original semaphore directory '{OG_semaphore_dir}' does not exist.")
randomized_dir = "assets/semaphores_randomized"
os.makedirs(randomized_dir, exist_ok=True)

# Step 1 : read the OG mapping file
# mapping: letter hand1 hand2 image.png
# ex : "A Low_Right Down A.png"
OG_mapping_file = "assets/semaphores/semaphores_mapping.txt"
OG_semaphores = {}
with open(OG_mapping_file, 'r') as f:
	lines = f.readlines()
	for line in lines:
		parts = line.strip().split()
		if len(parts) == 4:
			letter, hand1, hand2, image_file = parts
			OG_semaphores[letter] = (hand1, hand2, image_file)
		else:
			print(f"Warning: Invalid line in mapping file: '{line.strip()}'")

# Step 2 : randomize the letters
letters = list(OG_semaphores.keys())
shuffled_letters = letters.copy()
random.shuffle(shuffled_letters)
randomized_semaphores = {}
for original_letter, shuffled_letter in zip(letters, shuffled_letters):
	randomized_semaphores[shuffled_letter] = OG_semaphores[original_letter]

# Step 3 : create the new images files
for letter in randomized_semaphores:
	_, _, image = randomized_semaphores[letter]
	# copy image
	original_image_file = os.path.join(OG_semaphore_dir, image)
	if not os.path.exists(original_image_file):
		print(f"Warning: Original image file '{original_image_file}' does not exist. Skipping.")
		continue
	new_image_file = os.path.join(randomized_dir, f"{letter}.png")
	with open(original_image_file, 'rb') as src_file:
		image_data = src_file.read()
	with open(new_image_file, 'wb') as dst_file:
		dst_file.write(image_data)

# Step 4 : create the new mapping file
randomized_mapping_file = "assets/semaphores_randomized/semaphores_mapping.txt"
with open(randomized_mapping_file, 'w') as f:
	for letter in sorted(randomized_semaphores.keys()):
		hand1, hand2, _ = randomized_semaphores[letter]
		f.write(f"{letter} {hand1} {hand2} {letter}.png\n")

# Step 5 : copy the other images and mapping file
other_images = ["CANCEL.png", "ERROR.png", "NONE.png", "NUMERIC.png", "SPACE.png"]
other_images += [f"unused_{i}.png" for i in range(2, 9)]
for image in other_images:
	original_image_file = os.path.join(OG_semaphore_dir, image)
	if not os.path.exists(original_image_file):
		print(f"Warning: Original image file '{original_image_file}' does not exist. Skipping.")
		continue
	new_image_file = os.path.join(randomized_dir, image)
	with open(original_image_file, 'rb') as src_file:
		image_data = src_file.read()
	with open(new_image_file, 'wb') as dst_file:
		dst_file.write(image_data)
# copy the other mapping file
other_mapping_file = "assets/semaphores/other_semaphores_mapping.txt"
if os.path.exists(other_mapping_file):
	with open(other_mapping_file, 'r') as src_file:
		mapping_data = src_file.read()
	new_other_mapping_file = "assets/semaphores_randomized/other_semaphores_mapping.txt"
	with open(new_other_mapping_file, 'w') as dst_file:
		dst_file.write(mapping_data)

print(f"Randomized semaphore images and mapping file created in '{randomized_dir}'")
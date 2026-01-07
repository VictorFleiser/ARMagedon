import pygame
import cv2
import mediapipe as mp
import numpy as np
import time

# --- PARAMETERS ---

# SEMAPHORES_PATH = "assets/semaphores/"
SEMAPHORES_PATH = "assets/semaphores_randomized/"

# --- Pygame setup ---
pygame.init()

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
PINK = (255, 100, 200)
PURPLE = (180, 100, 255)

# --- Fonts ---
pygame.font.init()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 72)

# --- Semaphores Images ---
semaphore_images = {}
for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
	semaphore_images[letter] = pygame.image.load(f"{SEMAPHORES_PATH}{letter}.png").convert_alpha()
semaphore_images["CANCEL"] = pygame.image.load(f"{SEMAPHORES_PATH}CANCEL.png").convert_alpha()
semaphore_images["ERROR"] = pygame.image.load(f"{SEMAPHORES_PATH}ERROR.png").convert_alpha()
semaphore_images["NONE"] = pygame.image.load(f"{SEMAPHORES_PATH}NONE.png").convert_alpha()
semaphore_images["NUMERIC"] = pygame.image.load(f"{SEMAPHORES_PATH}NUMERIC.png").convert_alpha()
semaphore_images["SPACE"] = pygame.image.load(f"{SEMAPHORES_PATH}SPACE.png").convert_alpha()
semaphore_images["BOMB"] = pygame.image.load(f"{SEMAPHORES_PATH}BOMB.png").convert_alpha()
for i in range(3, 9):
	semaphore_images[f"unused_{i}"] = pygame.image.load(f"{SEMAPHORES_PATH}unused_{i}.png").convert_alpha()

# --- Semaphore Positions ---
semaphores_mapping = {}
with open(f"{SEMAPHORES_PATH}semaphores_mapping.txt", 'r') as f:
	lines = f.readlines()
	for line in lines:
		parts = line.strip().split()
		if len(parts) == 4:
			letter, hand1, hand2, _ = parts
			semaphores_mapping[(hand1, hand2)] = letter
			semaphores_mapping[(hand2, hand1)] = letter
with open(f"{SEMAPHORES_PATH}other_semaphores_mapping.txt", 'r') as f:
	lines = f.readlines()
	for line in lines:
		parts = line.strip().split()
		if len(parts) == 4:
			letter, hand1, hand2, _ = parts
			semaphores_mapping[(hand1, hand2)] = letter
			semaphores_mapping[(hand2, hand1)] = letter

# --- Bonus Icons ---
life_images = []
bomb_images = []
for i in range(5):
	life_images.append(pygame.image.load(f"assets/bonus/life_{i}.png").convert_alpha())
	bomb_images.append(pygame.image.load(f"assets/bonus/bomb_{i}.png").convert_alpha())

# --- Missiles Images ---
# TODO: create the missile images and load them here
missiles_images = []


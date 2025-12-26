import pygame
import cv2
import mediapipe as mp
import numpy as np
import time

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
	semaphore_images[letter] = pygame.image.load(f"assets/semaphores/{letter}.png").convert_alpha()
semaphore_images["CANCEL"] = pygame.image.load("assets/semaphores/CANCEL.png").convert_alpha()
semaphore_images["ERROR"] = pygame.image.load("assets/semaphores/ERROR.png").convert_alpha()
semaphore_images["NONE"] = pygame.image.load("assets/semaphores/NONE.png").convert_alpha()
semaphore_images["NUMERIC"] = pygame.image.load("assets/semaphores/NUMERIC.png").convert_alpha()
semaphore_images["SPACE"] = pygame.image.load("assets/semaphores/SPACE.png").convert_alpha()
for i in range(1, 9):
	semaphore_images[f"unused_{i}"] = pygame.image.load(f"assets/semaphores/unused_{i}.png").convert_alpha()

# --- Bonus Icons ---
life_images = []
bomb_images = []
for i in range(5):
	life_images.append(pygame.image.load(f"assets/bonus/life_{i}.png").convert_alpha())
	bomb_images.append(pygame.image.load(f"assets/bonus/bomb_{i}.png").convert_alpha())

# --- Missiles Images ---
# TODO: create the missile images and load them here
missiles_images = []


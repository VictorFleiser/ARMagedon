
import pygame

from game.menus.button import Button
from game.UI.webcam_section import WebcamPanel
from game.logger import DummyLogger

class MainMenu():
	def __init__(self, screen, start_game_callback):
		self.screen = screen
		self.start_game_callback = start_game_callback
		self.font = pygame.font.SysFont(None, 72)
		self.small_font = pygame.font.SysFont(None, 36)

		# menus possible : Start, Calibration, Profiles, Tutorial
		self.menu = "Start" 

		# Setup :
		self.dummyLogger = DummyLogger()
		self.setup_start_menu()
		self.setup_calibration()
		self.setup_profiles_menu()
		self.tutorial_setup()


	def setup_start_menu(self):
		# 3 Buttons : Start, Calibration, Quit
		screen_width, screen_height = self.screen.get_size()
		button_width, button_height = 300, 75
		button_x = (screen_width - button_width) // 2
		start_button_y = screen_height // 2 - button_height - 20
		calibration_button_y = screen_height // 2
		quit_button_y = screen_height // 2 + button_height + 20

		self.start_button = Button((button_x, start_button_y, button_width, button_height), "Start Game", self.font, lambda: setattr(self, 'menu', 'Profiles'))
		self.calibration_button = Button((button_x, calibration_button_y, button_width, button_height), "Calibration", self.font, lambda: setattr(self, 'menu', 'Calibration'))
		self.quit_button = Button((button_x, quit_button_y, button_width, button_height), "Quit", self.font, lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)))

	def setup_profiles_menu(self):
		# 3 Buttons : Load Profile, New Profile, Back
		screen_width, screen_height = self.screen.get_size()
		button_width, button_height = 300, 75
		button_x = (screen_width - button_width) // 2
		load_button_y = screen_height // 2 - button_height - 20
		new_button_y = screen_height // 2
		back_button_y = screen_height // 2 + button_height + 20

		self.load_profile_button = Button((button_x, load_button_y, button_width, button_height), "Load Profile", self.font, lambda: print("TODO: Load Profile clicked"))
		self.new_profile_button = Button((button_x, new_button_y, button_width, button_height), "New Profile", self.font, lambda: setattr(self, 'menu', 'Tutorial'))
		self.back_button2 = Button((button_x, back_button_y, button_width, button_height), "Back", self.font, lambda: setattr(self, 'menu', 'Start'))

	def setup_calibration(self):
		# Show Webcam feed in top left corner, with text instructions below, an image in the top right corner, and back button in bottom right corner
		self.calibration_image = pygame.image.load("assets/instruction_images/calibration_image.png")
		
		# --- Layout computation ---
		# Values needed for layout
		screen_width, screen_height = self.screen.get_size()
		# padding = 5
		webcam_aspect_ratio = 16 / 9  # assuming webcam feed is 16:9
		image_aspect_ratio = self.calibration_image.get_width() / self.calibration_image.get_height()
		button_width, button_height = 200, 50

		# calculate layout
		row1_height = int(screen_width / (webcam_aspect_ratio + image_aspect_ratio))
		# Compute Row 1 rects
		webcam_width = int(row1_height * webcam_aspect_ratio)
		image_width  = screen_width - webcam_width  # force exact fit
		self.webcam_rect = pygame.Rect(0, 0, webcam_width, row1_height)
		self.image_rect  = pygame.Rect(webcam_width, 0, image_width, row1_height)
		# Compute Row 2 rects
		row2_height = screen_height - row1_height
		self.instructions_rect = pygame.Rect(0, row1_height, screen_width - button_width, row2_height)
		self.back_button_rect = pygame.Rect(self.instructions_rect.right, screen_height - button_height, button_width, button_height)
		
		# Create back button
		self.back_button = Button(self.back_button_rect, "Back", self.font, lambda: setattr(self, 'menu', 'Start'))

		# Webcam :
		self.webcam_section = WebcamPanel(self.webcam_rect, self.dummyLogger)
		self.frame, detected_semaphore = self.webcam_section.update()
		
		# Image scaling
		self.calibration_image = pygame.transform.scale(self.calibration_image, (self.image_rect.width, self.image_rect.height))

	def tutorial_setup(self):
		# Start button to start the game
		screen_width, screen_height = self.screen.get_size()
		button_width, button_height = 300, 75
		button_x = (screen_width - button_width) // 2
		start_button_y = screen_height - button_height - 50
		self.tutorial_start_button = Button((button_x, start_button_y, button_width, button_height), "Start Game", self.font, self.start_game_callback)

	def draw(self):
		# Background
		self.screen.fill((0, 0, 0))

		match self.menu:
			case "Start":
				self.draw_start_menu()
			case "Calibration":
				self.draw_calibration_menu()
			case "Profiles":
				self.draw_profiles_menu()
			case "Tutorial":
				self.draw_tutorial_menu()
	
	def draw_start_menu(self):
		# 3 Buttons : Start, Calibration, Quit
		self.start_button.draw(self.screen)
		self.calibration_button.draw(self.screen)
		self.quit_button.draw(self.screen)

	def draw_calibration_menu(self):
		# Webcam feed rectangle
		self.frame, detected_semaphore = self.webcam_section.update()
		self.webcam_section.draw(self.screen, self.frame)
		# Add semi-transparent red border on top of webcam feed (inside border)
		border_thickness = 16
		pygame.draw.rect(self.screen, (255, 0, 0, 128), self.webcam_rect, border_thickness)
		# Instructions rectangle
		instructions_text = self.small_font.render("Calibration Instructions (TODO)", True, (255, 255, 255))
		instructions_rect_text = instructions_text.get_rect(center=self.instructions_rect.center)
		self.screen.blit(instructions_text, instructions_rect_text)
		# Image rectangle
		self.screen.blit(self.calibration_image, self.image_rect)
		# Back button
		self.back_button.draw(self.screen)

	def draw_profiles_menu(self):
		# 3 Buttons : Load Profile, New Profile, Back
		self.load_profile_button.draw(self.screen)
		self.new_profile_button.draw(self.screen)
		self.back_button2.draw(self.screen)

	def draw_tutorial_menu(self):
		self.tutorial_start_button.draw(self.screen)

	def handle_event(self, event):
		match self.menu:
			case "Start":
				self.start_button.handle_event(event)
				self.calibration_button.handle_event(event)
				self.quit_button.handle_event(event)
			case "Calibration":
				self.back_button.handle_event(event)
			case "Profiles":
				self.load_profile_button.handle_event(event)
				self.new_profile_button.handle_event(event)
				self.back_button2.handle_event(event)
			case "Tutorial":
				self.tutorial_start_button.handle_event(event)
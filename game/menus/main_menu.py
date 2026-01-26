
import pygame

from game.menus.button import Button
from game.UI.webcam_section import WebcamPanel
from game.logger import DummyLogger
from game.profile_manager import ProfileManager
from game.menus.profile_selection_menu import ProfileSelectionMenu
from game.menus.tutorial_screen import TutorialScreen

class MainMenu():
    def __init__(self, screen, start_game_callback):
        self.screen = screen
        self.start_game_callback = start_game_callback
        self.font = pygame.font.SysFont(None, 72)
        self.small_font = pygame.font.SysFont(None, 36)

        # Load sunset background for title screen
        self.title_background = pygame.image.load("assets/sprites/gameplay_bg_sunset.jpg").convert()

        self.profile_manager = ProfileManager()
        self.selected_profile = None

        # menus possible : Start, Calibration, Profiles, Tutorial
        self.menu = "Start" 

        # Setup :
        self.dummyLogger = DummyLogger()
        self.setup_start_menu()
        self.setup_calibration()
        self.setup_profiles_menu()
        self.tutorial_screen = None  # Will be created when needed

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'webcam_section'):
            self.webcam_section.close()
        if self.tutorial_screen:
            self.tutorial_screen.close()

    def toggle_hard_mode(self):
        print("Toggling hard mode")
        self.profile_selection.hard_mode = not self.profile_selection.hard_mode

    def setup_start_menu(self):
        # 3 Buttons : Start, Calibration, Quit
        screen_width, screen_height = self.screen.get_size()
        button_width, button_height = 300, 75
        button_x = (screen_width - button_width) // 2
        start_button_y = screen_height // 2 - button_height - 20
        hard_mode_button_y = screen_height // 2
        calibration_button_y = screen_height // 2 + button_height + 20
        quit_button_y = screen_height // 2 + 2 * (button_height + 20)

        self.start_button = Button((button_x, start_button_y, button_width, button_height), "Start Game", self.font, lambda: setattr(self, 'menu', 'Profiles'))
        self.hard_mode_button = Button((button_x, hard_mode_button_y, button_width, button_height), "Hard Mode", self.font, self.toggle_hard_mode)
        self.calibration_button = Button((button_x, calibration_button_y, button_width, button_height), "Calibration", self.font, lambda: setattr(self, 'menu', 'Calibration'))
        self.quit_button = Button((button_x, quit_button_y, button_width, button_height), "Quit", self.font, lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)))

    def setup_profiles_menu(self):
        screen_rect = pygame.Rect(0, 0, *self.screen.get_size())
        self.profile_selection = ProfileSelectionMenu(screen_rect, self.profile_manager)

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

    def setup_tutorial(self):
        """Initialize tutorial screen for new players"""
        screen_rect = pygame.Rect(0, 0, *self.screen.get_size())
        self.tutorial_screen = TutorialScreen(screen_rect, self.dummyLogger)

    def draw(self):
        # Background
        self.screen.fill((0, 0, 0))
        # assets/sprites/gameplay_bg_day.jpg image
        if self.profile_selection.hard_mode:
            # resize to screen size
            self.screen.blit(pygame.transform.scale(pygame.image.load("assets/sprites/gameplay_bg_hard.jpg").convert(), self.screen.get_size()), (0, 0))
        else:
            self.screen.blit(pygame.transform.scale(pygame.image.load("assets/sprites/gameplay_bg_day.jpg").convert(), self.screen.get_size()), (0, 0))

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
        # Draw sunset background with low opacity
        screen_width, screen_height = self.screen.get_size()
        background = pygame.transform.scale(self.title_background, (screen_width, screen_height))
        
        # Create a semi-transparent version
        background.set_alpha(30)  # Very low opacity (0-255, 30 is quite low)
        self.screen.blit(background, (0, 0))
        
        # Draw title "ARMagedon"
        title_text = self.font.render("ARMagedon", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(screen_width // 2, screen_height // 4))
        self.screen.blit(title_text, title_rect)
        
        # 3 Buttons : Start, Calibration, Quit
        # 4 Buttons : Start, Hard Mode, Calibration, Quit
        self.start_button.draw(self.screen)
        self.hard_mode_button.draw(self.screen)
        self.calibration_button.draw(self.screen)
        self.quit_button.draw(self.screen)

    def draw_calibration_menu(self):
        # black bg
        self.screen.fill((0, 0, 0))
        # Webcam feed rectangle
        self.frame, detected_semaphore = self.webcam_section.update()
        self.webcam_section.draw(self.screen, self.frame)
        # Add semi-transparent red border on top of webcam feed (inside border)
        border_thickness = 16
        pygame.draw.rect(self.screen, (255, 0, 0, 128), self.webcam_rect, border_thickness)
        # Instructions rectangle
        instructions_text = self.small_font.render("Step back from the camera to fit in the frame", True, (255, 255, 255))
        instructions_rect_text = instructions_text.get_rect(center=self.instructions_rect.center)
        self.screen.blit(instructions_text, instructions_rect_text)
        # Image rectangle
        self.screen.blit(self.calibration_image, self.image_rect)
        # Back button
        self.back_button.draw(self.screen)

    def draw_profiles_menu(self):
        # Draw profile selection UI
        self.profile_selection.draw(self.screen)

    def draw_tutorial_menu(self):
        """Draw the tutorial screen"""
        if self.tutorial_screen:
            self.tutorial_screen.update()
            self.tutorial_screen.draw(self.screen)
            
            if self.tutorial_screen.completed:
                # Mark tutorial as completed in profile
                self.profile_manager.current_profile['tutorial_completed'] = True
                self.profile_manager.save_profile()
                # pygame.time.wait(1000)
                self.start_game_callback()

    def handle_event(self, event):
        # Global key handlers
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                self.webcam_section.toggle_blur()
            elif event.key == pygame.K_t:
                self.webcam_section.toggle_display_mode()
        
        match self.menu:
            case "Start":
                self.start_button.handle_event(event)
                self.hard_mode_button.handle_event(event)
                self.calibration_button.handle_event(event)
                self.quit_button.handle_event(event)
            case "Calibration":
                self.back_button.handle_event(event)
            case "Profiles":
                result = self.profile_selection.handle_event(event)
                if result:
                    action, data = result
                    if action == "load":
                        # Load the selected profile
                        self.profile_manager.load_profile(data['filepath'])
                        self.selected_profile = data
                        # Apply long-term decay based on time since last session
                        self.profile_manager.apply_long_term_decay()
                        
                        # Check if tutorial was completed
                        if not self.profile_manager.current_profile.get('tutorial_completed', False):
                            # First time player - show tutorial
                            self.setup_tutorial()
                            self.menu = "Tutorial"
                        else:
                            # Tutorial already completed - start game
                            self.start_game_callback()
                    elif action == "create":
                        # Create new profile with selected number and hard mode flag
                        profile_num, hard_mode = data
                        profile = self.profile_manager.create_profile(profile_num, hard_mode=hard_mode)
                        self.selected_profile = profile
                        
                        if hard_mode:
                            # Hard mode profiles skip tutorial
                            self.profile_manager.current_profile['tutorial_completed'] = True
                            self.profile_manager.save_profile()
                            self.start_game_callback()
                        else:
                            # New normal profiles need to complete tutorial
                            self.setup_tutorial()
                            self.menu = "Tutorial"
                    elif action == "delete":
                        # Delete profile
                        self.profile_manager.delete_profile(data['filepath'])
                        self.profile_selection.refresh_profiles()
                    elif action == "back":
                        self.menu = "Start"
            case "Tutorial":
                if self.tutorial_screen:
                    self.tutorial_screen.handle_event(event)
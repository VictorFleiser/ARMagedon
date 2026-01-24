import pygame
from datetime import datetime
from game.logger import GameplayLogger, WebcamLogger
from game.game_clock import GameClock
from game.audio_manager import AudioManager
from game.UI.status_section import StatusPanel
from game.UI.semaphore_detected_section import SemaphorePanel
from game.UI.bonus_bar_section import BonusBar
from game.UI.webcam_section import WebcamPanel
from game.gameplay_section import Gameplay
from game.menus.pause_screen import PauseScreen
from game.menus.level_transition_screen import LevelTransitionScreen


def setup_game(screen, current_profile, profile_manager):
    """Initialize all game components and return them as a dict"""
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # Initialize loggers
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    profile_number = current_profile.get('profile_number', 0)
    gameplay_logger = GameplayLogger(f"logs/gameplay_logs_p{profile_number}_{timestamp}.jsonl")
    webcam_logger = WebcamLogger(f"logs/webcam_logs_{timestamp}.jsonl")
    
    # Initialize audio manager
    audio_manager = AudioManager()

    # Initialize game clock
    game_clock = GameClock(gameplay_logger, webcam_logger, audio_manager)
    
    # --- Layout computation ---
    game_col_width = SCREEN_HEIGHT  # Square gameplay area
    ui_col_width = SCREEN_WIDTH - game_col_width
    
    # Row heights
    row4_height = SCREEN_HEIGHT // 2
    row3_height = 20
    remaining_height = SCREEN_HEIGHT - (row4_height + row3_height)
    row1_height = remaining_height // 2
    row2_height = remaining_height - row1_height
    
    # --- Instantiate panels ---
    hard_mode = current_profile.get('hard_mode', False)
    gameplay_section = Gameplay(pygame.Rect(0, 0, game_col_width, SCREEN_HEIGHT), gameplay_logger, game_clock, audio_manager, hard_mode)
    status_section = StatusPanel(pygame.Rect(game_col_width, 0, ui_col_width, row1_height), gameplay_logger)
    semaphore_section = SemaphorePanel(pygame.Rect(game_col_width, row1_height, ui_col_width, row2_height))
    bonus_section = BonusBar(pygame.Rect(game_col_width, row1_height + row2_height, ui_col_width, row3_height))
    webcam_section = WebcamPanel(pygame.Rect(game_col_width, row1_height + row2_height + row3_height, ui_col_width, row4_height), webcam_logger)
    pause_screen = PauseScreen(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), game_clock)
    level_transition_screen = LevelTransitionScreen(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), game_clock)
    
    # Start background music
    audio_manager.play_music(volume=0.1, hard_mode=hard_mode)
    
    # Cross-references
    gameplay_section.status_panel = status_section
    gameplay_section.bonus_bar = bonus_section
    gameplay_section.semaphore_panel = semaphore_section
    gameplay_section.profile_manager = profile_manager
    
    # Load profile data
    load_profile_data(current_profile, gameplay_section, status_section, level_transition_screen, gameplay_logger)
    
    return {
        'gameplay_section': gameplay_section,
        'status_section': status_section,
        'semaphore_section': semaphore_section,
        'bonus_section': bonus_section,
        'webcam_section': webcam_section,
        'pause_screen': pause_screen,
        'level_transition_screen': level_transition_screen,
        'game_clock': game_clock,
        'audio_manager': audio_manager,
        'gameplay_logger': gameplay_logger
    }


def load_profile_data(current_profile, gameplay_section, status_section, level_transition_screen, gameplay_logger):
    """Load profile data into game components"""
    # P(K) always starts at P(L0) - no loading from profile
    
    # Load success_score from profile
    if current_profile.get('success_score'):
        print("Loading success_score from profile...")
        for letter, score in current_profile['success_score'].items():
            if letter in gameplay_section.spawner.bkt.success_score:
                gameplay_section.spawner.bkt.success_score[letter] = score
    
    # Load current level from profile
    saved_level = current_profile.get('current_level', 0)
    if saved_level > 0 and gameplay_section.spawner.use_level_progression:
        print(f"Restoring to level {saved_level}...")
        gameplay_section.spawner.advance_to_level(saved_level)
    
    # Stats (lives, bombs, score) are reset every session - no loading
    
    # Initialize first level transition (only for new players)
    if gameplay_section.spawner.use_level_progression and gameplay_section.spawner.level_definitions and saved_level == 0:
        first_level_letters = gameplay_section.spawner.level_definitions[0]
        level_transition_screen.start_transition(1, first_level_letters, [])
        gameplay_logger.level_transition_started(1, first_level_letters)
    
    print(f"Starting at level {gameplay_section.spawner.get_current_level() + 1} with letters: {gameplay_section.spawner.unlocked_letters}")

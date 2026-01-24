import pygame

class GameClock:
    def __init__(self, gameplay_logger, webcam_logger, audio_manager):
        self.gameplay_logger = gameplay_logger
        self.webcam_logger = webcam_logger
        self.last_time = pygame.time.get_ticks()
        self.paused = False
        self.audio_manager = audio_manager
        
        # 2 types of pauses : 1 for when the player presses escape, another for level transitions
        self.button_paused = False
        self.transition_paused = False

    def pause(self, reason):
        # Set appropriate pause flag
        if reason == "player_paused":
            self.button_paused = True
            self.audio_manager.pause_music()
        elif reason == "level_transition":
            self.transition_paused = True
        else:
            print(f"Unknown pause reason: {reason}")
            return
        self.paused = True

        # Log pause event
        self.gameplay_logger.pause(reason)
        self.webcam_logger.pause(reason)

    def resume(self, reason):
        if reason == "player_resumed":
            self.button_paused = False
            self.audio_manager.resume_music()
        elif reason == "level_transition_complete":
            self.transition_paused = False
        else:
            print(f"Unknown resume reason: {reason}")
            return
        # Only unpause if both pause flags are false
        if not self.button_paused and not self.transition_paused:
            self.paused = False

            # Log resume event
            self.gameplay_logger.resume(reason)
            self.webcam_logger.resume(reason)

            # Reset reference so dt does NOT include paused duration
            self.last_time = pygame.time.get_ticks()

    def get_dt(self):
        if self.paused:
            return 0.0

        now = pygame.time.get_ticks()
        dt = (now - self.last_time) / 1000.0
        self.last_time = now
        return dt

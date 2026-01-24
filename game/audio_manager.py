import pygame
from pathlib import Path

class AudioManager:
    def __init__(self):
        """Initialize the audio manager and load sounds."""
        pygame.mixer.init()
        
        self.sounds_dir = Path("assets/sounds")
        self.sounds = {}
        self.music_playing = False
        
        # Try to load sound effects
        self._load_sound_effect("explosion", "explosion.ogg")
        self._load_sound_effect("missile_hit", "missile_hit.ogg")
        self._load_sound_effect("powerup_life", "powerup_life.ogg")
        self._load_sound_effect("powerup_bomb", "powerup_bomb.ogg")
        self._load_sound_effect("powerup_protection", "powerup_protection.ogg")

        # Store music file path (will be set when play_music is called)
        self.music_file = None
    
    def _find_music_file(self, hard_mode=False):
        """Find the gameplay music file."""
        music_name = "gameplay_music_hard.ogg" if hard_mode else "gameplay_music.ogg"
        path = self.sounds_dir / music_name
        if path.exists():
            return str(path)
        return None
    
    def _load_sound_effect(self, name, filename):
        """Load a sound effect """
        path = self.sounds_dir / filename
        if path.exists():
            try:
                self.sounds[name] = pygame.mixer.Sound(str(path))
                print(f"[Audio] Loaded sound effect: {filename}")
                return
            except Exception as e:
                print(f"[Audio] Error loading {filename}: {e}")
        else:
            print(f"[Audio] Sound effect '{name}' not found: {filename}")
    
    def play_music(self, volume=0.3, hard_mode=False):
        """Start playing background music (loops indefinitely)."""
        self.music_file = self._find_music_file(hard_mode)
        if self.music_file and not self.music_playing:
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                self.music_playing = True
                print(f"[Audio] Playing music: {self.music_file}")
            except Exception as e:
                print(f"[Audio] Error playing music: {e}")
        elif not self.music_file:
            print("[Audio] No music file found")
    
    def stop_music(self):
        """Stop playing background music."""
        if self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False
    
    def pause_music(self):
        """Pause background music."""
        if self.music_playing:
            pygame.mixer.music.pause()
    
    def resume_music(self):
        """Resume background music."""
        if self.music_playing:
            pygame.mixer.music.unpause()
    
    def play_sound(self, sound_name, volume=0.5):
        """Play a sound effect."""
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]
            sound.set_volume(volume)
            sound.play()
    
    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)."""
        pygame.mixer.music.set_volume(volume)
    
    def set_sound_volume(self, sound_name, volume):
        """Set volume for a specific sound effect (0.0 to 1.0)."""
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(volume)

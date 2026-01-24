import pygame
from assets.assets import semaphore_images

class LevelTransitionScreen:
    def __init__(self, screen_rect, game_clock):
        self.screen_rect = screen_rect
        self.game_clock = game_clock
        self.huge_font = pygame.font.SysFont(None, 240)
        self.font = pygame.font.SysFont(None, 64)
        self.small_font = pygame.font.SysFont(None, 56)
        self.tiny_font = pygame.font.SysFont(None, 40)
        
        self.gameplay_width = screen_rect.height
        
        # Overlay for gameplay section only (semi-transparent)
        self.gameplay_overlay = pygame.Surface((self.gameplay_width, screen_rect.height))
        self.gameplay_overlay.set_alpha(150)
        self.gameplay_overlay.fill((255, 255, 255))
        
        # State
        self.active = False
        self.new_letters = []
        self.all_unlocked_letters = []
        self.completed_new_letters = set()
        self.current_level = 0
        
        # Countdown state
        self.countdown_active = False
        self.countdown_timer = 0.0
        self.countdown_value = 3
        self.last_ticks = 0 # for countdown timing independent of game clock
        
    def start_transition(self, level, new_letters, all_unlocked_letters):
        """Start a level transition with given letters"""
        self.active = True
        self.current_level = level
        self.new_letters = new_letters
        self.all_unlocked_letters = all_unlocked_letters
        self.completed_new_letters = set()
        self.countdown_active = False
        self.countdown_timer = 0.0
        self.countdown_value = 3
        
        self.game_clock.pause("level_transition") # Pause game
    
    def check_semaphore_input(self, semaphore):
        """Check if user completed one of the new semaphores"""
        if not self.active or self.countdown_active:
            return
        
        if semaphore in self.new_letters and semaphore not in self.completed_new_letters:
            self.completed_new_letters.add(semaphore)
            
            if len(self.completed_new_letters) == len(self.new_letters): # All completed
                self.start_countdown()
    
    def start_countdown(self):
        self.countdown_active = True
        self.countdown_timer = 0.0
        self.countdown_value = 3
        self.last_ticks = pygame.time.get_ticks()
    
    def update(self, dt):
        """Update countdown if active"""
        if not self.countdown_active:
            return False
        
        # Real time based countdown
        now = pygame.time.get_ticks()
        dt_real = (now - self.last_ticks) / 1000.0
        self.last_ticks = now
        
        self.countdown_timer += dt_real
        
        # Update countdown value
        new_value = 3 - int(self.countdown_timer)
        if new_value != self.countdown_value and new_value >= 0:
            self.countdown_value = new_value
        
        if self.countdown_timer >= 3.0:
            self.end_transition()
            return True
        
        return False
    
    def end_transition(self):
        """End the level transition and resume game"""
        self.active = False
        self.countdown_active = False
        self.game_clock.resume("level_transition_complete")
    
    def draw(self, surface):
        """Draw the level transition screen"""
        if not self.active:
            return
        
        surface.blit(self.gameplay_overlay, (0, 0))
        
        gameplay_center_x = self.gameplay_width // 2
        
        if self.countdown_active: # Show countdown
            if self.countdown_value > 0:
                countdown_text = self.huge_font.render(str(self.countdown_value), True, (0, 0, 0))
                countdown_rect = countdown_text.get_rect(center=(gameplay_center_x, self.screen_rect.centery))
                surface.blit(countdown_text, countdown_rect)
            return
        
        # Level title
        level_text = self.font.render(f"Level {self.current_level}", True, (0, 0, 0))
        level_rect = level_text.get_rect(center=(gameplay_center_x, 30))
        surface.blit(level_text, level_rect)
        
        # All letters
        self.draw_all_letters_by_level(surface, gameplay_center_x)
        
        # Instruction
        lines = ["Complete all new semaphores", "to continue:"]
        y_offset = 230 - 15  # start a bit higher to center the block
        for line in lines:
            instruction_text = self.small_font.render(line, True, (60, 60, 60))
            instruction_rect = instruction_text.get_rect(center=(gameplay_center_x, y_offset))
            surface.blit(instruction_text, instruction_rect)
            y_offset += 30
        # New semaphores
        new_semaphore_y = 270
        new_semaphore_size = 150
        spacing = 20
        
        # ( 2 rows if more than 3 new letters )
        max_per_row = 3
        num_letters = len(self.new_letters)
        
        for i, letter in enumerate(self.new_letters):
            row = i // max_per_row
            col = i % max_per_row
            
            items_in_row = min(max_per_row, num_letters - row * max_per_row)
            row_width = items_in_row * (new_semaphore_size + spacing) - spacing
            row_start_x = gameplay_center_x - row_width // 2
            
            x = row_start_x + col * (new_semaphore_size + spacing)
            y = new_semaphore_y + row * (new_semaphore_size + spacing + 50)
            
            # Semaphore images
            if letter in semaphore_images:
                img = semaphore_images[letter]
                img_scaled = pygame.transform.scale(img, (new_semaphore_size, new_semaphore_size))
                img_rect = img_scaled.get_rect(center=(x + new_semaphore_size // 2, y + new_semaphore_size // 2))

                bg_color = (50, 150, 50) if letter in self.completed_new_letters else (255, 255, 255) # Green if completed, white otherwise
                bg_rect = pygame.Rect(x - 5, y - 5, new_semaphore_size + 10, new_semaphore_size + 10)
                pygame.draw.rect(surface, bg_color, bg_rect, border_radius=10)
                
                surface.blit(img_scaled, img_rect)
                
                letter_text = self.small_font.render(letter, True, (0, 0, 0))
                letter_rect = letter_text.get_rect(center=(x + new_semaphore_size // 2, y + new_semaphore_size + 30))
                surface.blit(letter_text, letter_rect)
    
    def draw_all_letters_by_level(self, surface, center_x):
        """Draw all unlocked letters grouped by level at the top"""
        from assets.assets import semaphore_images
        
        levels_to_show = []
        for level_idx, level_letters in enumerate(self.all_unlocked_letters):
            if isinstance(level_letters, list):
                levels_to_show.append((level_idx + 1, level_letters))
            else: # flat list: need to reconstruct levels (but shouldn't happen when using levels)
                break
        
        if not levels_to_show: # If all_unlocked_letters is flat, reconstruct from current level
            for level_idx in range(self.current_level):
                if level_idx < len(self.all_unlocked_letters):
                    levels_to_show.append((level_idx + 1, [self.all_unlocked_letters[level_idx]]))
        
        semaphore_size = 40
        spacing = 8
        start_y = 70
        max_width = self.gameplay_width - 40 # margins
        
        current_x = 20 # start with left margin
        current_row = 0
        row_height = semaphore_size + 30 # with space for label
        
        # Previous letters
        for letter in self.all_unlocked_letters:
            if letter in self.new_letters:
                continue # skip, they're shown in the center
            
            if current_x + semaphore_size > max_width:
                current_row += 1
                current_x = 20
            
            y_pos = start_y + current_row * row_height
            
            if letter in semaphore_images:
                img = semaphore_images[letter]
                img_scaled = pygame.transform.scale(img, (semaphore_size, semaphore_size))
                img_rect = img_scaled.get_rect(topleft=(current_x, y_pos))
                
                surface.blit(img_scaled, img_rect)
                
                letter_text = self.tiny_font.render(letter, True, (80, 80, 80))
                letter_rect = letter_text.get_rect(center=(current_x + semaphore_size // 2, y_pos + semaphore_size + 10))
                surface.blit(letter_text, letter_rect)
            
            current_x += semaphore_size + spacing

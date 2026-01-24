"""
Tutorial screen for first-time players
"""
import pygame
from game.UI.webcam_section import WebcamPanel
from assets.assets import SEMAPHORES_PATH


class TutorialScreen:
    def __init__(self, screen_rect, webcam_logger):
        self.screen_rect = screen_rect
        self.webcam_logger = webcam_logger
        
        self.stage = 0 # 0: Intro/A, 1: Mechanics explanation
        self.completed = False
        self.current_frame = None
        
        self.title_font = pygame.font.SysFont(None, 72)
        self.text_font = pygame.font.SysFont(None, 60) # normal text
        self.small_font = pygame.font.SysFont(None, 50)
        
        self.semaphore_a = pygame.image.load(f"{SEMAPHORES_PATH}A.png").convert_alpha()
        self.semaphore_b = pygame.image.load(f"{SEMAPHORES_PATH}B.png").convert_alpha()
        self.semaphore_c = pygame.image.load(f"{SEMAPHORES_PATH}C.png").convert_alpha()
        self.missile_img = pygame.image.load("assets/sprites/missile.png").convert_alpha()
        self.bonus_life = pygame.image.load("assets/bonus/life_1.png").convert_alpha()
        self.bonus_bomb = pygame.image.load("assets/bonus/bomb_1.png").convert_alpha()
        self.bonus_protection = pygame.image.load("assets/building_patterns/building_pattern_1/00_00_2.png").convert_alpha()
        self.explosion_sprite = pygame.image.load("assets/sprites/explosion.png").convert_alpha()

        from game.audio_manager import AudioManager
        self.audio_manager = AudioManager()
        
        from game.effects.explosion import ExplosionEffect
        self.ExplosionEffect = ExplosionEffect
        self.explosion = None
        self.missile_destroyed = False
        self.missile_cooldown = 0.0
        self.missile_respawn_time = 5.0
        
        self.mechanics_image = self._create_mechanics_image()
        
        # Setup webcam for semaphore detection
        webcam_width = int(screen_rect.height * 0.35 * (16/9))
        webcam_height = int(screen_rect.height * 0.35)
        webcam_x = screen_rect.width - webcam_width - 40
        webcam_y = 120
        self.webcam_rect = pygame.Rect(webcam_x, webcam_y, webcam_width, webcam_height)
        self.webcam_section = WebcamPanel(self.webcam_rect, webcam_logger)
        
        self.a_completed = False
        self.c_completed = False
        
        self.hold_time = 0.0
        self.required_hold_time = 1.5
        self.last_detected = None
        self.current_detected = "NONE"
        self.last_update_time = pygame.time.get_ticks()
        
        self.c_hold_time = 0.0
    
    def _create_mechanics_image(self):
        """ Visual explanation of game mechanics """
        width, height = 700, 650
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((20, 20, 40))
        
        font = pygame.font.SysFont(None, 40)
        title_font = pygame.font.SysFont(None, 48)
        label_font = pygame.font.SysFont(None, 48)
        
        # Title
        title = title_font.render("Game Mechanics", True, (255, 255, 100))
        surface.blit(title, (width//2 - title.get_width()//2, 20))
        y = 90
        
        mechanics = [
            "• Missiles fall with letters on them",
            "• Match the semaphore to destroy missiles",
            "• Hints appear as missiles fall",
            "• Destroy before hints for more points!",
        ]
        
        for line in mechanics:
            text = font.render(line, True, (200, 200, 200))
            surface.blit(text, (40, y))
            y += 45
        
        # Show missile with letter example on the right side
        missile_scale = 1.0
        scaled_missile = pygame.transform.scale(
            self.missile_img,
            (int(self.missile_img.get_width() * missile_scale),
             int(self.missile_img.get_height() * missile_scale))
        )
        self.demo_missile_x = width - scaled_missile.get_width() - 30
        self.demo_missile_y = 140
        self.scaled_missile = scaled_missile
        
        # Bonuses section
        y += 30
        bonus_title = title_font.render("Bonuses:", True, (100, 255, 100))
        surface.blit(bonus_title, (40, y))
        y += 50
        bonus_subtitle = font.render("Every 3000 points, gain a random bonus:", True, (200, 200, 200))
        surface.blit(bonus_subtitle, (40, y))
        y += 50
        
        # Life bonus
        icon_size = 50
        life_icon = pygame.transform.scale(self.bonus_life, (icon_size, icon_size))
        surface.blit(life_icon, (60, y))
        label = label_font.render("Life:", True, (255, 255, 100))
        surface.blit(label, (130, y))
        text = font.render("Gain extra lives", True, (200, 200, 200))
        surface.blit(text, (250, y + 5))
        y += 70
        
        # Bomb bonus
        bomb_icon = pygame.transform.scale(self.bonus_bomb, (icon_size, icon_size))
        surface.blit(bomb_icon, (60, y))
        label = label_font.render("Bomb:", True, (255, 255, 100))
        surface.blit(label, (130, y))
        text = font.render("Destroy all missiles", True, (200, 200, 200))
        surface.blit(text, (280, y + 5))
        y += 70
        
        # Protection bonus
        protection_icon = pygame.transform.scale(self.bonus_protection, (icon_size, icon_size))
        surface.blit(protection_icon, (60, y))
        label = label_font.render("Shield:", True, (255, 255, 100))
        surface.blit(label, (130, y))
        text = font.render("Protect buildings", True, (200, 200, 200))
        surface.blit(text, (280, y + 5))
        
        return surface
    
    def check_semaphore(self, semaphore):
        """ Check if the correct semaphore was detected """
        if self.stage == 0 and semaphore == "A" and not self.a_completed:
            self.a_completed = True
            return True
        elif self.stage == 1 and semaphore == "B" and self.c_completed:
            self.completed = True
            return True
        return False
    
    def advance_stage(self):
        """ Move to the next tutorial stage """
        if self.stage == 0 and self.a_completed:
            self.stage = 1
            self.hold_time = 0.0
    
    def update(self):
        """ Update webcam and check for semaphore detection """
        self.current_frame, detected_semaphore = self.webcam_section.update()
        self.current_detected = detected_semaphore
        
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_update_time) / 1000.0
        self.last_update_time = current_time
        
        # Update explosion if active
        if self.explosion:
            self.explosion.update(dt)
            if not self.explosion.alive:
                self.explosion = None
        
        # Update missile cooldown
        if self.missile_cooldown > 0:
            self.missile_cooldown -= dt
            if self.missile_cooldown <= 0: # respawn
                self.missile_destroyed = False
                self.c_hold_time = 0.0
        
        # C semaphore
        if self.stage == 1 and detected_semaphore == "C" and not self.missile_destroyed:
            self.c_hold_time += dt
            
            if self.c_hold_time >= self.required_hold_time:
                self.missile_destroyed = True
                self.missile_cooldown = self.missile_respawn_time
                self.c_completed = True
                # explosion
                missile_center_x = self.demo_missile_x + self.scaled_missile.get_width()//2
                missile_center_y = self.demo_missile_y + self.scaled_missile.get_height()//2
                self.explosion = self.ExplosionEffect((missile_center_x, missile_center_y), self.explosion_sprite)
                self.audio_manager.play_sound("explosion", volume=0.8)
        else:
            self.c_hold_time = max(0, self.c_hold_time - dt)
        
        # A or B semaphore
        target_semaphore = "A" if self.stage == 0 else ("B" if (self.stage == 1 and self.c_completed) else None)
        if target_semaphore and detected_semaphore == target_semaphore:
            self.hold_time += dt
            self.last_detected = detected_semaphore
            
            if self.hold_time >= self.required_hold_time:
                if self.check_semaphore(detected_semaphore):
                    # Completed!
                    self.hold_time = 0.0
                    pygame.time.wait(300)
                    if self.stage == 0:
                        self.advance_stage()
        else:
            self.hold_time = max(0, self.hold_time - dt)
            self.last_detected = detected_semaphore
    
    def draw(self, surface):
        """ Draw the tutorial screen """
        surface.fill((10, 10, 30))
        
        if self.stage == 0:
            self._draw_stage_a(surface)
        elif self.stage == 1:
            self._draw_mechanics(surface)
    
    def _draw_stage_a(self, surface):
        """Draw stage 0: Learn semaphore A"""
        # Title
        title = self.title_font.render("Welcome to ARMagedon!", True, (255, 255, 100))
        surface.blit(title, (self.screen_rect.width//2 - title.get_width()//2, 40))
        
        # Instructions (left)
        instructions = [
            "Step back from the camera to",
            "fit in the frame.",
            "",
            "Use your arms to create",
            "semaphore signals to",
            "destroy incoming missiles!",
            "",
            "Let's start with the letter A:",
        ]
        
        y = 140
        for line in instructions:
            text = self.text_font.render(line, True, (200, 200, 200))
            surface.blit(text, (60, y))
            y += 50
        
        # Show semaphore A image (left) with white background
        img_scale = 0.16
        w, h = self.semaphore_a.get_size()
        scaled_img = pygame.transform.scale(self.semaphore_a, (int(w * img_scale), int(h * img_scale)))
        padding = 10
        bg_rect = pygame.Rect(80, y, scaled_img.get_width() + padding*2, scaled_img.get_height() + padding*2)
        pygame.draw.rect(surface, (255, 255, 255), bg_rect)
        pygame.draw.rect(surface, (200, 200, 200), bg_rect, 2) # border
        surface.blit(scaled_img, (90, y + padding))
        
        # webcam (right side)
        if self.current_frame is not None:
            self.webcam_section.draw(surface, self.current_frame)
            # Show detected semaphore
            if self.current_detected and self.current_detected != "NONE":
                detected_text = self.text_font.render(f"Detected: {self.current_detected}", True, (100, 255, 255))
                text_x = self.webcam_rect.centerx - detected_text.get_width() // 2
                text_y = self.webcam_rect.y - 50
                surface.blit(detected_text, (text_x, max(90, text_y)))
        
        # Progress bar below webcam
        if not self.a_completed:
            progress = min(1.0, self.hold_time / self.required_hold_time)
            bar_width = self.webcam_rect.width - 20
            bar_height = 36
            bar_x = self.webcam_rect.x + 10
            bar_y = self.webcam_rect.bottom + 20
            
            # Background
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Progress
            if progress > 0:
                pygame.draw.rect(surface, (100, 255, 100), (bar_x, bar_y, int(bar_width * progress), bar_height))
            pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)
            progress_text = self.small_font.render(f"Hold: {int(progress * 100)}%", True, (255, 255, 255))
            surface.blit(progress_text, (bar_x + bar_width//2 - progress_text.get_width()//2, bar_y + 5))
        
        # status
        if self.a_completed:
            status = self.text_font.render("Great!", True, (100, 255, 100))
        else:
            status = self.small_font.render("Hold semaphore A until the bar fills", True, (255, 200, 100))
        surface.blit(status, (self.screen_rect.width//2 - status.get_width()//2, self.screen_rect.height - 80))
    
    def _draw_mechanics(self, surface):
        """ Draw stage 1: Explain game mechanics, missile C, use B to continue """
        # Title
        title = self.title_font.render("How to Play", True, (255, 255, 100))
        surface.blit(title, (50, 40))
        
        # mechanics image (left side)
        img_x = 50
        img_y = 120
        
        # copy to draw missile on
        mechanics_display = self.mechanics_image.copy()
        
        # Only draw missile/hint/letter if not destroyed
        if not self.missile_destroyed:
            # missile
            mechanics_display.blit(self.scaled_missile, (self.demo_missile_x, self.demo_missile_y))
            
            # C
            letter_text = self.title_font.render("C", True, (0, 0, 0))
            letter_x = self.demo_missile_x + self.scaled_missile.get_width()//2 - letter_text.get_width()//2
            letter_y = self.demo_missile_y + self.scaled_missile.get_height()//2 - letter_text.get_height()//2
            mechanics_display.blit(letter_text, (letter_x, letter_y))
            
            # hint if not completed
            if not self.c_completed:
                hint_scale = 0.1
                w, h = self.semaphore_c.get_size()
                scaled_hint = pygame.transform.scale(self.semaphore_c, (int(w * hint_scale), int(h * hint_scale)))
                hint_x = self.demo_missile_x + self.scaled_missile.get_width()//2 - scaled_hint.get_width()//2
                hint_y = self.demo_missile_y - scaled_hint.get_height() - 10
                hint_bg = pygame.Rect(hint_x - 5, hint_y - 5, scaled_hint.get_width() + 10, scaled_hint.get_height() + 10)
                pygame.draw.rect(mechanics_display, (255, 255, 255), hint_bg)
                pygame.draw.rect(mechanics_display, (150, 150, 150), hint_bg, 2)
                mechanics_display.blit(scaled_hint, (hint_x, hint_y))
        
        surface.blit(mechanics_display, (img_x, img_y))
        
        # explosion
        if self.explosion:
            explosion_surface = pygame.Surface(self.mechanics_image.get_size(), pygame.SRCALPHA)
            self.explosion.draw(explosion_surface)
            surface.blit(explosion_surface, (img_x, img_y))
        
        # webcam (right side)
        if self.current_frame is not None:
            self.webcam_section.draw(surface, self.current_frame)
            # Show detected semaphore
            if self.current_detected and self.current_detected != "NONE":
                detected_text = self.text_font.render(f"Detected: {self.current_detected}", True, (100, 255, 255))
                text_x = self.webcam_rect.centerx - detected_text.get_width() // 2
                text_y = self.webcam_rect.y - 50
                surface.blit(detected_text, (text_x, text_y))
        
        # B image below webcam
        if self.c_completed:
            img_scale = 0.13
            w, h = self.semaphore_b.get_size()
            scaled_b = pygame.transform.scale(self.semaphore_b, (int(w * img_scale), int(h * img_scale)))
            b_x = self.webcam_rect.centerx - scaled_b.get_width()//2
            b_y = self.webcam_rect.bottom + 70
            if b_y + scaled_b.get_height() > self.screen_rect.height - 100:
                b_y = self.screen_rect.height - scaled_b.get_height() - 110
            padding = 10
            bg_rect = pygame.Rect(b_x - padding, b_y - padding, scaled_b.get_width() + padding*2, scaled_b.get_height() + padding*2)
            pygame.draw.rect(surface, (255, 255, 255), bg_rect)
            pygame.draw.rect(surface, (200, 200, 200), bg_rect, 2)
            surface.blit(scaled_b, (b_x, b_y))
            b_label = self.small_font.render("Semaphore B", True, (200, 200, 200))
            surface.blit(b_label, (b_x + scaled_b.get_width()//2 - b_label.get_width()//2, b_y + scaled_b.get_height() + 10))
            
            # Progress bar
            if not self.completed:
                progress = min(1.0, self.hold_time / self.required_hold_time)
                bar_width = self.webcam_rect.width - 20
                bar_height = 36
                bar_x = self.webcam_rect.x + 10
                bar_y = self.webcam_rect.bottom + 20
                
                # Background
                pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
                # Progress
                if progress > 0:
                    pygame.draw.rect(surface, (100, 255, 100), (bar_x, bar_y, int(bar_width * progress), bar_height))
                pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)
                progress_text = self.small_font.render(f"Hold B: {int(progress * 100)}%", True, (255, 255, 255))
                surface.blit(progress_text, (bar_x + bar_width//2 - progress_text.get_width()//2, bar_y + 5))
            
            if self.completed:
                status = self.text_font.render("Perfect! Starting game...", True, (100, 255, 100))
                status_x = b_x + scaled_b.get_width()//2 - status.get_width()//2
                status_y = b_y + scaled_b.get_height() + 50
                surface.blit(status, (status_x, status_y))
            else:
                status_y = b_y + scaled_b.get_height() + 50
                lines = ["Hold semaphore B to", "start the game"]
                y_offset = status_y
                for line in lines:
                    text = self.small_font.render(line, True, (255, 200, 100))
                    surface.blit(text, (b_x + scaled_b.get_width()//2 - text.get_width()//2, y_offset))
                    y_offset += 30
        else:
            status_y = self.webcam_rect.bottom + 80
            lines = ["First, destroy the demo missile", "with C"]
            y_offset = status_y
            for line in lines:
                text = self.small_font.render(line, True, (255, 200, 100))
                surface.blit(text, (self.webcam_rect.centerx - text.get_width()//2, y_offset))
                y_offset += 30
            
            # Progress bar for C
            progress = min(1.0, self.c_hold_time / self.required_hold_time)
            bar_width = self.webcam_rect.width - 20
            bar_height = 36
            bar_x = self.webcam_rect.x + 10
            bar_y = status_y + 100
            
            # Background
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Progress
            if progress > 0:
                pygame.draw.rect(surface, (100, 255, 100), (bar_x, bar_y, int(bar_width * progress), bar_height))
            pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)
            progress_text = self.small_font.render(f"Hold C: {int(progress * 100)}%", True, (255, 255, 255))
            surface.blit(progress_text, (bar_x + bar_width//2 - progress_text.get_width()//2, bar_y + 5))
    
    def close(self):
        if hasattr(self, 'webcam_section'):
            self.webcam_section.close()
        if hasattr(self, 'audio_manager'):
            self.audio_manager.stop_music() # probably not needed but just in case. TODO: delete AudioManager instance?
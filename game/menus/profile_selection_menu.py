"""
Profile Selection Menu for ARMagedon
Allows creating, loading, and deleting profiles
"""
import pygame
from game.profile_manager import ProfileManager

class ProfileSelectionMenu:
    def __init__(self, screen_rect, profile_manager):
        self.screen_rect = screen_rect
        self.profile_manager = profile_manager
        
        self.title_font = pygame.font.SysFont(None, 64)
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
        self.profiles = []
        self.selected_profile = None
        self.mode = "select" # "select" or "create"
        
        # UI elements
        self.profile_rects = []
        self.delete_buttons = []
        self.create_button_rect = None
        self.back_button_rect = None
        self.new_profile_buttons = []
        
        self.refresh_profiles()
    
    def refresh_profiles(self):
        """Reload the list of profiles"""
        self.profiles = self.profile_manager.list_profiles()
    
    def draw(self, surface):
        """Draw the profile selection menu"""
        surface.fill((20, 20, 40))
        
        if self.mode == "select":
            self.draw_profile_list(surface)
        elif self.mode == "create":
            self.draw_create_profile(surface)
    
    def draw_profile_list(self, surface):
        """Draw the list of existing profiles"""
        # Title
        title_text = self.title_font.render("Select Profile", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen_rect.centerx, 50))
        surface.blit(title_text, title_rect)
        
        # Profile list
        self.profile_rects = []
        self.delete_buttons = []
        
        start_y = 150
        profile_height = 100
        spacing = 20
        
        for i, profile in enumerate(self.profiles):
            y = start_y + i * (profile_height + spacing)
            
            # Profile box
            profile_rect = pygame.Rect(50, y, self.screen_rect.width - 150, profile_height)
            pygame.draw.rect(surface, (60, 60, 80), profile_rect, border_radius=10)
            pygame.draw.rect(surface, (100, 100, 120), profile_rect, width=2, border_radius=10)
            self.profile_rects.append(profile_rect)
            
            # Profile info
            profile_num = profile.get('profile_number', '?')
            player_name = profile.get('player_name', 'Player')
            level = profile.get('current_level', 0) + 1  # Display level (1-indexed)
            
            # Profile number and name
            name_text = self.font.render(f"Profile {profile_num}: {player_name}", True, (255, 255, 255))
            surface.blit(name_text, (profile_rect.x + 20, profile_rect.y + 15))
            
            # Level and stats
            level_text = self.small_font.render(f"Level {level}", True, (200, 200, 200))
            surface.blit(level_text, (profile_rect.x + 20, profile_rect.y + 50))
            
            # Last played
            from datetime import datetime
            try:
                last_played = datetime.fromisoformat(profile.get('last_played', ''))
                last_played_str = last_played.strftime("%Y-%m-%d %H:%M")
            except:
                last_played_str = "Unknown"
            
            last_played_text = self.small_font.render(f"Last played: {last_played_str}", True, (180, 180, 180))
            surface.blit(last_played_text, (profile_rect.x + 200, profile_rect.y + 50))
            
            # Playtime
            playtime = profile.get('total_playtime_seconds', 0)
            playtime_str = self.profile_manager.format_playtime(playtime)
            playtime_text = self.small_font.render(f"Playtime: {playtime_str}", True, (180, 180, 180))
            surface.blit(playtime_text, (profile_rect.x + 500, profile_rect.y + 50))
            
            # Delete button
            delete_button = pygame.Rect(profile_rect.right - 120, profile_rect.y + 30, 100, 40)
            pygame.draw.rect(surface, (150, 50, 50), delete_button, border_radius=5)
            delete_text = self.small_font.render("Delete", True, (255, 255, 255))
            delete_text_rect = delete_text.get_rect(center=delete_button.center)
            surface.blit(delete_text, delete_text_rect)
            self.delete_buttons.append(delete_button)
        
        # Create new profile button
        self.create_button_rect = pygame.Rect(
            self.screen_rect.centerx - 150,
            start_y + len(self.profiles) * (profile_height + spacing) + 30,
            300, 60
        )
        pygame.draw.rect(surface, (50, 150, 50), self.create_button_rect, border_radius=10)
        create_text = self.font.render("Create New Profile", True, (255, 255, 255))
        create_text_rect = create_text.get_rect(center=self.create_button_rect.center)
        surface.blit(create_text, create_text_rect)
        
        # Back button
        self.back_button_rect = pygame.Rect(50, self.screen_rect.height - 100, 150, 50)
        pygame.draw.rect(surface, (100, 100, 100), self.back_button_rect, border_radius=5)
        back_text = self.font.render("Back", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        surface.blit(back_text, back_text_rect)
    
    def draw_create_profile(self, surface):
        """Draw the create new profile screen"""
        # Title
        title_text = self.title_font.render("Create New Profile", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen_rect.centerx, 50))
        surface.blit(title_text, title_rect)
        
        # Instruction
        instruction_text = self.font.render("Select a profile slot (1-5):", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(self.screen_rect.centerx, 150))
        surface.blit(instruction_text, instruction_rect)
        
        # Profile slot buttons
        self.new_profile_buttons = []
        button_size = 100
        spacing = 40
        total_width = 5 * button_size + 4 * spacing
        start_x = self.screen_rect.centerx - total_width // 2
        start_y = 250
        
        for i in range(1, 6):
            button_rect = pygame.Rect(
                start_x + (i - 1) * (button_size + spacing),
                start_y,
                button_size,
                button_size
            )
            
            # Check if slot is already taken
            slot_taken = any(p.get('profile_number') == i for p in self.profiles)
            
            color = (80, 80, 80) if slot_taken else (50, 100, 150)
            pygame.draw.rect(surface, color, button_rect, border_radius=10)
            
            # Profile number
            number_text = self.title_font.render(str(i), True, (255, 255, 255))
            number_rect = number_text.get_rect(center=button_rect.center)
            surface.blit(number_text, number_rect)
            
            if slot_taken:
                taken_text = self.small_font.render("Taken", True, (200, 150, 150))
                taken_rect = taken_text.get_rect(center=(button_rect.centerx, button_rect.bottom + 20))
                surface.blit(taken_text, taken_rect)
            
            self.new_profile_buttons.append((button_rect, i, slot_taken))
        
        # Back button
        self.back_button_rect = pygame.Rect(
            self.screen_rect.centerx - 75,
            self.screen_rect.height - 100,
            150, 50
        )
        pygame.draw.rect(surface, (100, 100, 100), self.back_button_rect, border_radius=5)
        back_text = self.font.render("Back", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        surface.blit(back_text, back_text_rect)
    
    def handle_event(self, event):
        """Handle mouse events for profile selection"""
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        
        pos = event.pos
        
        if self.mode == "select":
            # Check delete buttons FIRST (before profile selection)
            for i, button in enumerate(self.delete_buttons):
                if button.collidepoint(pos):
                    return ("delete", self.profiles[i])
            
            # Check profile selection
            for i, rect in enumerate(self.profile_rects):
                if rect.collidepoint(pos):
                    return ("load", self.profiles[i])
            
            # Check create button
            if self.create_button_rect and self.create_button_rect.collidepoint(pos):
                self.mode = "create"
                return None
            
            # Check back button
            if self.back_button_rect and self.back_button_rect.collidepoint(pos):
                return ("back", None)
        
        elif self.mode == "create":
            # Check profile slot buttons
            for button_rect, profile_num, slot_taken in self.new_profile_buttons:
                if button_rect.collidepoint(pos) and not slot_taken:
                    return ("create", profile_num)
            
            # Check back button
            if self.back_button_rect and self.back_button_rect.collidepoint(pos):
                self.mode = "select"
                return None
        
        return None

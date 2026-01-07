import pygame
import cv2
import mediapipe as mp
import numpy as np
import time
import random

from assets.assets import WHITE, font
from game.missiles.missile import Missile
from game.missiles.spawner_random_pick import RandomPickSpawner
from game.missiles.spawner_bkt_pick import BKTPickSpawner
from game.effects.explosion import ExplosionEffect
from game.effects.floating_text import FloatingTextEffect
from game.other_gameplay.buildings import BuildingGrid

class Gameplay:
    def __init__(self, rect, gameplay_logger):
        # --- Initialization ---
        self.background_image = pygame.image.load("assets/sprites/gameplay_bg.png").convert()
        self.grid_size = 10
        self.rect = rect
        self.gameplay_logger = gameplay_logger
        # # --- Debug mode (terminal display from the initial code back in september/october) ---
        # self.debug_terminal = False
        # self.font = pygame.font.SysFont("Consolas", 18)
        # self.logs = []
        # self.max_logs = 25
        # self.last_ground_hit_time = time.time()

        # --- Grid computation ---
        self.cell_size = self.rect.width // self.grid_size
        self.grid_origin = self.rect.topleft

        # Example grid state (0 = intact, 1 = destroyed)
        self.grid = [
            [0 for _ in range(self.grid_size)]
            for _ in range(self.grid_size)
        ]

        # --- Buildings ---
        self.building_pattern_path = "assets/building_patterns/building_pattern_2"
        self.buildings = BuildingGrid(self.grid_size, self.rect, self.building_pattern_path)

        # self.spawner = RandomPickSpawner(gameplay=self, available_letters=["A", "E", "I", "O", "U"])
        # --- Missile spawner (BKT-based) ---
        self.spawner = BKTPickSpawner(
            gameplay=self,
            available_letters=list("EAISNRTOLUDCMPGBVHFQYXJKWZ"),
            initial_number_of_letters_tested=1,
            overall_knowledge_threshold=0.5,
            spawn_interval=4.0,
            speed_range=(12.5, 12.5),
            hint_min=0.3,
            hint_max=0.8,
            focus_weak_prob=0.8,
            ignore_correct_after_hint=True,
            bkt_params={
                'p_l0': 0.0, # Initial probability of knowing
                'p_t': 0.1, # Transition/learning probability
                'p_s': 0.1, # Slip probability
                'p_g': 0.25, # Guess probability
                'base_decay_rate': 0.05, # knowledge decay rate
                'stability_factor': 0.8 # stability factor for decay adjustment
            }
        )

        # --- Effects ---
        self.effects = []
        self.explosion_sprite = pygame.image.load("assets/sprites/explosion.png").convert_alpha()


        # Links to other sections (assigned by main)
        self.status_panel = None
        self.bonus_bar = None
        self.semaphore_panel = None

        self.missiles = []

        self.missile_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.score_font = pygame.font.SysFont("Arial", 20, bold=True)

        self.last_time = pygame.time.get_ticks()
        
        self.bkt_snapshot_interval = 5.0
        self.bkt_snapshot_timer = 0.0

    # # -------------------------------------------------------
    # #                     Terminal Logging helper
    # # -------------------------------------------------------
    # def log(self, text):
    #     # used to log to the debug terminal on the gameplay section
    #     self.logs.append(f"{text}")
    #     if len(self.logs) > self.max_logs:
    #         self.logs.pop(0)

    # -------------------------------------------------------
    #                 Event simulation functions
    # -------------------------------------------------------
    def bonus_bar_filled(self):
        pass
        # kind = "life" if random.random() < 0.5 else "bomb"
        # self.log(f"<- bonus bar filled : spawning a {kind} missile")


    def resolve_bonus_event(self):
        pass
    #     kind = getattr(self, "pending_kind", "life")
    #     if kind == "life":
    #         self.log("-> life missile destroyed : life fragment obtained")
    #         if self.status_panel:
    #             self.status_panel.gain_life_fragments(1)
    #     else:
    #         self.log("-> bomb missile destroyed : bomb fragment obtained")
    #         if self.status_panel:
    #             self.status_panel.gain_bomb_fragments(1)

    def semaphore_input(self, semaphore_detected):
        destroyed = []

        # logging
        self.gameplay_logger.semaphore_completed(semaphore_detected)

        # check for bomb usage
        bomb_used = False
        if semaphore_detected == "BOMB":
            bomb_used = self.status_panel.use_bomb(1)

        for missile in self.missiles:
            if bomb_used:
                destroyed.append(missile)
            elif missile.letter == semaphore_detected:
                destroyed.append(missile)

        for missile in destroyed:
            score = self.compute_missile_score(
                missile,
                bomb_used=bomb_used
            )

            # logging
            self.gameplay_logger.missile_destroyed(missile, (missile.y - missile.start_y) / missile.distance, score, bomb_used)
            
            # Update BKT model
            if isinstance(self.spawner, BKTPickSpawner):
                if bomb_used:
                    self.spawner.on_missile_destroyed_bomb(missile.letter)
                elif self.spawner.ignore_correct_after_hint and missile.shown_hint_flag: # If hint was shown & toggle on, don't update BKT as 'correct'
                    pass # nothing for now (maybe log later)
                else:
                    self.spawner.on_missile_destroyed_correct(missile.letter)
                    missile.bkt_updated_flag = True
            
            self.status_panel.gain_score(score)
            missile.alive = False
            pos = (missile.x, missile.y)

            self.effects.append(
                ExplosionEffect(pos, self.explosion_sprite)
            )

            self.effects.append(
                FloatingTextEffect(
                    pos,
                    f"+{score}",
                    self.score_font,
                    (255, 255, 0)
                )
            )

        # if semaphore_detected == "BOMB":
        #     self.log("<- semaphore [BOMB] input : using a bomb to destroy all missiles")
        #     self.log("-> consume 1 bomb")
        #     # self.log("-> all missiles on screen destroyed : increase score by +200")
        #     if self.status_panel:
        #         self.status_panel.use_bomb(1)
        #         # self.status_panel.gain_score(200)
        # else:
        #     self.log(f"<- semaphore [{semaphore_detected}] input : destroying all [{semaphore_detected}] missiles")
        #     # self.log(f"-> all [{semaphore_detected}] missiles destroyed : increase score by +100")
        #     # if self.status_panel:
        #     #     self.status_panel.gain_score(100)

    def gameover(self):
        # self.log("<- gameover!") # skip since error
        pass 

    # -------------------------------------------------------
    #                    Update loop
    # -------------------------------------------------------
    def update(self):
        now = pygame.time.get_ticks()
        dt = (now - self.last_time) / 1000.0
        self.last_time = now

        for missile in self.missiles:
            if missile.update(dt):
                # missile hit the ground
                if isinstance(self.spawner, BKTPickSpawner):
                    if not missile.bkt_updated_flag:
                        self.spawner.on_missile_hit_ground(missile.letter)
                        missile.bkt_updated_flag = True
                break   # missile hit the ground; do not check for collisions (we already reset the map)
            col, row = self.missile_grid_position(missile)

            if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                status = self.buildings.grid[row][col]

                if status == 2:
                    # missile reached a building
                    self.buildings.grid[row][col] = 1   # change sprite to damaged
                    self.buildings.grid[row+1][col] = 0 # remove damaged sprite above
                    missile.alive = False
                    # update BKT for building hit (miss) - only if not already updated
                    if isinstance(self.spawner, BKTPickSpawner):
                        if not missile.bkt_updated_flag:
                            self.spawner.on_missile_hit_ground(missile.letter)
                            missile.bkt_updated_flag = True
                    # logging
                    self.gameplay_logger.missile_hit_ground(missile, (missile.y - missile.start_y) / missile.distance)

        self.spawner.update(dt)

        self.missiles = [m for m in self.missiles if m.alive]



        for effect in self.effects:
            effect.update(dt)

        self.effects = [e for e in self.effects if e.alive]
        
        # BKT logging
        if isinstance(self.spawner, BKTPickSpawner):
            self.bkt_snapshot_timer += dt
            if self.bkt_snapshot_timer >= self.bkt_snapshot_interval:
                self.bkt_snapshot_timer = 0.0
                bkt_state = self.spawner.get_bkt_state()
                self.gameplay_logger.bkt_state_snapshot(bkt_state, verbose=True)

    # -------------------------------------------------------
    #                        Draw
    # -------------------------------------------------------
    def draw(self, surface, debug_mode=False):
        # if self.debug_terminal:
        #     self.draw_terminal(surface)
        # else:
        self.draw_gameplay(surface, debug_mode)

    # # -------------------------------------------------------
    # #                TERMINAL DEBUG VIEW
    # # -------------------------------------------------------
    # def draw_terminal(self, surface):
    #     pygame.draw.rect(surface, (10, 10, 10), self.rect)
    #     x, y = self.rect.x + 10, self.rect.y + 10
    #     for i, line in enumerate(self.logs[-self.max_logs:]):
    #         txt = self.font.render(line, True, (0, 255, 0))
    #         surface.blit(txt, (x, y + i * 20))

    # -------------------------------------------------------
    #                GAMEPLAY VISUAL VIEW
    # -------------------------------------------------------
    def draw_transparent_rect(self, surface, color, rect):
        """Draws a semi-transparent rectangle on the given surface."""
        # color should be (R, G, B, A)
        shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
        pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
        surface.blit(shape_surf, rect)

    def draw_gameplay(self, surface, debug_mode=False):
        # --- Background ---
        bg = pygame.transform.smoothscale(
            self.background_image,
            (self.rect.width, self.rect.height)
        )
        surface.blit(bg, self.rect.topleft)

        # --- Grid overlay (visible for now) ---
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cell_x = self.grid_origin[0] + col * self.cell_size
                # cell_y = self.grid_origin[1] + row * self.cell_size
                cell_y = self.grid_origin[1] + (self.grid_size - 1 - row) * self.cell_size

                cell_rect = pygame.Rect(
                    cell_x, cell_y,
                    self.cell_size, self.cell_size
                )

                # Color based on state
                if self.buildings.grid[row][col] == 0:
                    color = (255, 255, 255, 40)
                elif self.buildings.grid[row][col] == 1:
                    color = (255, 200, 80, 100)
                else:
                    color = (255, 80, 80, 100)

                pygame.draw.rect(surface, color, cell_rect, 1)
        
        # --- Missiles ---
        for missile in self.missiles:
            missile.draw(surface)
            
            # Missile debug info (only in debug mode)
            if debug_mode:
                progress = (missile.y - missile.start_y) / missile.distance
                
                # Get BKT parameters for this missile's letter
                debug_lines = [
                    f"Pos: {progress:.3f}",
                    f"Hint: {missile.hint_start:.2f}",
                ]
                
                if isinstance(self.spawner, BKTPickSpawner):
                    p_k = self.spawner.bkt.get_knowledge(missile.letter)
                    s_s = self.spawner.bkt.success_score.get(missile.letter, 0)
                    p_l0 = self.spawner.bkt.p_l0
                    p_t = self.spawner.bkt.p_t
                    p_s = self.spawner.bkt.p_s
                    p_g = self.spawner.bkt.p_g
                    debug_lines.extend([
                        f"P(K): {p_k:.2f} (S: {s_s})",
                        f"P(L0): {p_l0:.2f}",
                        f"P(T): {p_t:.2f}",
                        f"P(S): {p_s:.2f}",
                        f"P(G): {p_g:.2f}"
                    ])
                
                # Draw missile info text
                debug_font = pygame.font.SysFont("Arial", 14)
                text_y = missile.y + 60
                for line in debug_lines:
                    if line:  # Only draw non-empty lines
                        text_surface = debug_font.render(line, True, (255, 255, 0))
                        text_rect = text_surface.get_rect(center=(missile.x, text_y))
                        # Draw background for readability
                        bg_rect = text_rect.inflate(4, 2)
                        self.draw_transparent_rect(surface, (0, 0, 0, 100), bg_rect)
                        surface.blit(text_surface, text_rect)
                        text_y += 16

        # --- Debug: Show all semaphores with P(K) ---
        if debug_mode and isinstance(self.spawner, BKTPickSpawner):
            debug_font_small = pygame.font.SysFont("Arial", 12)
            x_offset = self.rect.left + 10
            y_offset = self.rect.top + 10
            
            # Get all letters and their knowledge
            all_letters = self.spawner.available_letters
            tested_count = self.spawner.number_of_letters_tested
            
            # Predict next selection probabilities
            next_probs = self.spawner.get_selection_probabilities()
            
            # Title
            title_surface = debug_font_small.render("Semaphore Knowledge:", True, (255, 255, 255))
            title_bg = pygame.Rect(x_offset - 2, y_offset - 2, title_surface.get_width() + 4, title_surface.get_height() + 4)
            self.draw_transparent_rect(surface, (0, 0, 0, 120), title_bg)
            surface.blit(title_surface, (x_offset, y_offset))
            y_offset += 18
            
            # List all letters
            for i, letter in enumerate(all_letters):
                p_k = self.spawner.bkt.get_knowledge(letter)
                s_s = self.spawner.bkt.success_score.get(letter, 0)
                prob = next_probs.get(letter, 0.0)
                
                # Grey out letters not yet tested
                if i >= tested_count:
                    color = (100, 100, 100)
                else:
                    color = (255, 255, 255)
                
                text = f"{letter}: {p_k:.3f} (S: {s_s}) [P: {prob:.2f}]"
                text_surface = debug_font_small.render(text, True, color)
                text_bg = pygame.Rect(x_offset - 2, y_offset - 2, text_surface.get_width() + 4, text_surface.get_height() + 4)
                self.draw_transparent_rect(surface, (0, 0, 0, 100), text_bg)
                surface.blit(text_surface, (x_offset, y_offset))
                y_offset += 14

        # --- Effects ---
        for effect in self.effects:
            effect.draw(surface)

        # --- Buildings ---
        self.buildings.draw(surface)

        # --- Shortcuts info (bottom left) ---
        shortcut_font = pygame.font.SysFont("Arial", 12)
        shortcut_text = "D: Debug | P: Profiler"
        shortcut_surface = shortcut_font.render(shortcut_text, True, (200, 200, 200))
        
        # Position at bottom-left corner
        sx = self.rect.left + 10
        sy = self.rect.bottom - shortcut_surface.get_height() - 10
        
        shortcut_bg = pygame.Rect(sx - 4, sy - 2, shortcut_surface.get_width() + 8, shortcut_surface.get_height() + 4)
        self.draw_transparent_rect(surface, (0, 0, 0, 100), shortcut_bg)
        surface.blit(shortcut_surface, (sx, sy))

    # -------------------------------------------------------
    #                  Missile management
    # -------------------------------------------------------

    def get_occupied_columns(self):
        occupied = set()
        for missile in self.missiles:
            occupied.add(missile.column)
        return occupied

    def get_active_letters(self):
        return {missile.letter for missile in self.missiles}

    def missile_grid_position(self, missile):
        col = int((missile.x - self.rect.left) / self.buildings.cell_width)
        row = int((self.rect.bottom - missile.y) / self.buildings.cell_height)
        return col, row


    # -------------------------------------------------------
    #              Scoring computation
    # -------------------------------------------------------

    def compute_missile_score(self, missile, bomb_used=False):
        # Score = how far the missile had progressed (100-0) : so if fully down = 0, at the start = 100
        # 10x if destroyed before hint shown
        # 0.1x if bomb used # REMOVED
        
        progress = (missile.y - missile.start_y) / missile.distance
        base_score = int((1.0 - progress) * 100)

        # # Bomb used
        # if bomb_used:
        #     base_score = base_score // 10
        # else :
        # Destroyed before hint
        if not missile.should_show_hint():
            base_score *= 10

        return base_score

    # -------------------------------------------------------
    #                  Gameplay
    # -------------------------------------------------------

    def take_damage(self):
        self.missiles.clear()
        self.effects.clear()
        self.reset_buildings()
        self.status_panel.take_damage()

    def reset_buildings(self):
        # reapply initial building pattern
        self.buildings = BuildingGrid(self.grid_size, self.rect, self.building_pattern_path)
    
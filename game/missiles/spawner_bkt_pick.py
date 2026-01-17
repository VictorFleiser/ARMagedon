"""
BKT-based spawner that adaptively selects letters based on user knowledge.
Focuses on letters the user knows least, and adjusts hint timing based on mastery.
"""
import random
import math
from game.missiles.missile_spawner import MissileSpawner
from game.missiles.bkt_model import BKTModel

class BKTPickSpawner(MissileSpawner):
    def __init__(
        self,
        gameplay,
        available_letters, # letters to spawn
        initial_number_of_letters_tested=1, # how many different letters to use at start
        overall_knowledge_threshold=0.5, # average knowledge to increase letter pool
        spawn_interval=3.0,
        speed_range=(10.0, 15.0), # missile (lower is faster)
        hint_min=0.3, # where hint can appear
        hint_max=0.8,
        ignore_correct_after_hint=True,
        bkt_params=None, # dict with BKT parameters (p_l0, p_t, p_s, p_g)
        use_level_progression=False, # whether to use level-based progression
        level_definitions=None # list of letter groups for each level
    ):
        super().__init__(gameplay)
        
        self.available_letters = available_letters
        self.number_of_letters_tested = initial_number_of_letters_tested
        self.overall_knowledge_threshold = overall_knowledge_threshold
        self.overall_knowledge = 0.0
        self.spawn_interval = spawn_interval
        self.speed_range = speed_range
        self.hint_min = hint_min
        self.hint_max = hint_max
        self.ignore_correct_after_hint = ignore_correct_after_hint
        
        # Level-based progression
        self.use_level_progression = use_level_progression
        self.level_definitions = level_definitions if level_definitions else []
        self.current_level = 0
        self.unlocked_letters = []
        
        # If using level progression, initialize with first level
        if self.use_level_progression and self.level_definitions:
            self.unlocked_letters = self.level_definitions[0].copy()
            self.number_of_letters_tested = len(self.unlocked_letters)
        
        # init BKT model
        if bkt_params is None:
            bkt_params = {}
        
        self.bkt = BKTModel(
            letters=available_letters,
            initial_number_of_letters_tested=self.number_of_letters_tested,
            p_l0=bkt_params.get('p_l0', 0.0), # 0 in theory
            p_t=bkt_params.get('p_t', 0.1),
            p_s=bkt_params.get('p_s', 0.1),
            p_g=bkt_params.get('p_g', 0.25),
            base_decay_rate=bkt_params.get('base_decay_rate', 0.02),
            stability_factor=bkt_params.get('stability_factor', 0.5)
        )
        
        self.timer = 0.0
        self.letters_history = []
    
    def get_selection_probabilities(self):
        """Calculate probabilities used for selecting the next letter based on current state."""
        free_letters = self.get_free_letters() # letters not on screen
        if free_letters is None: return {}
        
        # Use unlocked letters if level progression is enabled, otherwise use the old method
        if self.use_level_progression:
            free_letters = list(set(free_letters) & set(self.unlocked_letters))
        else:
            free_letters = list(set(free_letters) & set(self.available_letters[:self.number_of_letters_tested]))
        
        if not free_letters: return {}
        
        # Softmax selection over (1 - knowledge) to focus on weakness
        temperature = 0.2
        weights = []
        for letter in free_letters:
            p_k = self.bkt.get_knowledge(letter)
            # We use (1-p_k) because we want lower knowledge to have higher weight
            weight = math.exp((1.0 - p_k) / temperature)
            weights.append(weight)
        
        sum_weights = sum(weights)
        probs = [w / sum_weights for w in weights]
        
        result = {letter: 0.0 for letter in self.available_letters}
        for letter, p in zip(free_letters, probs):
            result[letter] = p
        return result

    def update(self, dt): # every frame
        self.timer += dt

        self.bkt.update_decay(dt)

        # Only auto-increase letters if NOT using level progression
        if not self.use_level_progression:
            if self.bkt.get_lowest_overall_knowledge() >= self.overall_knowledge_threshold:
                # increase letter pool if possible
                if self.number_of_letters_tested < len(self.available_letters):
                    self.number_of_letters_tested += 1
                    self.bkt.number_of_letters_tested = self.number_of_letters_tested
        
        if self.timer >= self.spawn_interval:
            self.timer -= self.spawn_interval
            self.spawn_adaptive_missile()
    
    def select_letter_adaptive(self):
        probs_dict = self.get_selection_probabilities()
        if not probs_dict:
            return None
        
        # Filter only those with non-zero probability (available and tested)
        letters = [l for l, p in probs_dict.items() if p > 0]
        weights = [p for l, p in probs_dict.items() if p > 0]
        
        if not letters:
            return None
            
        return random.choices(letters, weights=weights, k=1)[0]
    
    def select_hint_timing(self, letter):
        """ Show hints based on P(K): lower knowledge = earlier hints, higher = later """
        p_k = self.bkt.get_knowledge(letter)
        base_hint = self.hint_min + p_k * (self.hint_max - self.hint_min)
        # randomness = random.uniform(-0.1, 0.1)
        hint_start = base_hint #+ randomness
        hint_start = max(self.hint_min, min(self.hint_max, hint_start))
        
        return hint_start
    
    def spawn_adaptive_missile(self):
        column = self.get_free_column()
        letter = self.select_letter_adaptive()
        
        print(f"[Spawner] spawn_adaptive_missile: column={column}, letter={letter}, unlocked={self.unlocked_letters}")
        
        if column is None or letter is None:
            print(f"[Spawner] Cannot spawn: column={column}, letter={letter}")
            return
        
        speed = random.uniform(*self.speed_range)
        hint_start = self.select_hint_timing(letter)
        
        self.spawn_missile(
            column=column,
            letter=letter,
            speed=speed,
            hint_start=hint_start
        )
        self.letters_history.append(letter)
        # print(f"Letters history: {self.letters_history}")
    
    def on_missile_destroyed_correct(self, letter):
        self.bkt.update_correct(letter)
        if hasattr(self.gameplay, 'gameplay_logger'):
            self.gameplay.gameplay_logger.bkt_update(
                letter=letter,
                outcome='correct',
                p_k=self.bkt.get_knowledge(letter),
                base_decay_rate=self.bkt.base_decay_rate,
                stability_factor=self.bkt.stability_factor
            )
    
    def on_missile_destroyed_bomb(self, letter): # we can ignore for now
        if hasattr(self.gameplay, 'gameplay_logger'):
            self.gameplay.gameplay_logger.bkt_update(
                letter=letter,
                outcome='bomb_ignore',
                p_k=self.bkt.get_knowledge(letter),
                base_decay_rate=self.bkt.base_decay_rate,
                stability_factor=self.bkt.stability_factor
            )
    
    def on_missile_hit_ground(self, letter):
        self.bkt.update_incorrect(letter)
        if hasattr(self.gameplay, 'gameplay_logger'):
            self.gameplay.gameplay_logger.bkt_update(
                letter=letter,
                outcome='incorrect',
                p_k=self.bkt.get_knowledge(letter),
                base_decay_rate=self.bkt.base_decay_rate,
                stability_factor=self.bkt.stability_factor
            )
    
    def on_missile_hint_shown(self, letter):
        """Called when a hint is shown for a missile - update BKT with incorrect"""
        self.bkt.update_incorrect(letter)
        if hasattr(self.gameplay, 'gameplay_logger'):
            self.gameplay.gameplay_logger.bkt_update(
                letter=letter,
                outcome='hint_shown',
                p_k=self.bkt.get_knowledge(letter),
                base_decay_rate=self.bkt.base_decay_rate,
                stability_factor=self.bkt.stability_factor
            )
    
    def get_bkt_state(self):
        """Get current BKT state for all letters."""
        return self.bkt.get_all_knowledge()
    
    def check_level_advancement(self):
        """Check if player should advance to the next level.
        Returns the next level number and new letters if ready, otherwise None.
		The gameplay section may have other criteria to validate level advancement."""
        if not self.use_level_progression:
            return None
        
        # Check if there's a next level
        if self.current_level >= len(self.level_definitions) - 1:
            return None  # Already at max level
        
        # Get all letters from all previous levels (including current)
        all_previous_letters = []
        for i in range(self.current_level + 1):
            all_previous_letters.extend(self.level_definitions[i])
        
        # Find the minimum knowledge among all previous letters
        min_knowledge = 1.0
        for letter in all_previous_letters:
            p_k = self.bkt.get_knowledge(letter)
            min_knowledge = min(min_knowledge, p_k)
        
        # Advance if minimum knowledge exceeds threshold (all letters are above threshold)
        if min_knowledge >= self.overall_knowledge_threshold:
            next_level = self.current_level + 1
            new_letters = self.level_definitions[next_level]
            return (next_level, new_letters)
        
        return None
    
    def advance_to_level(self, level):
        """Manually advance to a specific level."""
        if not self.use_level_progression or level >= len(self.level_definitions):
            print(f"[Spawner] advance_to_level({level}) rejected: use_level_progression={self.use_level_progression}, len(defs)={len(self.level_definitions)}")
            return
        
        self.current_level = level
        
        # Unlock all letters up to and including this level
        self.unlocked_letters = []
        for i in range(level + 1):
            self.unlocked_letters.extend(self.level_definitions[i])
        
        self.number_of_letters_tested = len(self.unlocked_letters)
        self.bkt.number_of_letters_tested = self.number_of_letters_tested
        
        print(f"[Spawner] Advanced to level {level}: unlocked_letters={self.unlocked_letters}, num_tested={self.number_of_letters_tested}")
    
    def get_current_level(self):
        """Get the current level number."""
        return self.current_level
    
    def get_unlocked_letters(self):
        """Get all currently unlocked letters."""
        return self.unlocked_letters.copy()

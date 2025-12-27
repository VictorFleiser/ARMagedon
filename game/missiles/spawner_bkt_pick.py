"""
BKT-based spawner that adaptively selects letters based on user knowledge.
Focuses on letters the user knows least, and adjusts hint timing based on mastery.
"""
import random
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
		focus_weak_prob=0.8, # 80% chance to pick from weakest letters
		bkt_params=None # dict with BKT parameters (p_l0, p_t, p_s, p_g)
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
		self.focus_weak_prob = focus_weak_prob
		
		# init BKT model
		if bkt_params is None:
			bkt_params = {}
		self.bkt = BKTModel(
			letters=available_letters,
			initial_number_of_letters_tested=initial_number_of_letters_tested,
			p_l0=bkt_params.get('p_l0', 0.0), # 0 in theory
			p_t=bkt_params.get('p_t', 0.1),
			p_s=bkt_params.get('p_s', 0.1),
			p_g=bkt_params.get('p_g', 0.25)
		)
		
		self.timer = 0.0
	
	def update(self, dt): # every frame
		self.timer += dt

		if self.bkt.get_lowest_overall_knowledge() >= self.overall_knowledge_threshold:
			# increase letter pool if possible
			if self.number_of_letters_tested < len(self.available_letters):
				self.number_of_letters_tested += 1
				self.bkt.number_of_letters_tested = self.number_of_letters_tested
		
		if self.timer >= self.spawn_interval:
			self.timer -= self.spawn_interval
			self.spawn_adaptive_missile()
	
	def select_letter_adaptive(self):
		free_letters = self.get_free_letters() # letters not on screen
		if free_letters is None: return None
		free_letters = list(set(free_letters) & set(self.available_letters[:self.number_of_letters_tested]))
		if not free_letters: return None
		
		if random.random() < self.focus_weak_prob: # focus on weakness
			# letter_knowledge = [(letter, self.bkt.get_knowledge(letter)) for letter in free_letters]
			# letter_knowledge.sort(key=lambda x: x[1]) # weakest first
			
			# n_candidates = min(3, len(letter_knowledge)) # top 3 weakest
			# candidates = [letter for letter, _ in letter_knowledge[:n_candidates]]
			# letter = random.choice(candidates)
			letter = random.choice(self.bkt.get_weakest_letters(n=2, all_letters=False))[0]
			if letter not in free_letters:
				letter = random.choice(free_letters)
		else: # random pick
			letter = random.choice(free_letters)
		
		return letter
	
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
		
		if column is None or letter is None:
			return
		
		speed = random.uniform(*self.speed_range)
		hint_start = self.select_hint_timing(letter)
		
		self.spawn_missile(
			column=column,
			letter=letter,
			speed=speed,
			hint_start=hint_start
		)
	
	def on_missile_destroyed_correct(self, letter):
		self.bkt.update_correct(letter)
		if hasattr(self.gameplay, 'gameplay_logger'):
			self.gameplay.gameplay_logger.bkt_update(
				letter=letter,
				outcome='correct',
				p_k=self.bkt.get_knowledge(letter)
			)
	
	def on_missile_destroyed_bomb(self, letter): # we can ignore for now
		if hasattr(self.gameplay, 'gameplay_logger'):
			self.gameplay.gameplay_logger.bkt_update(
				letter=letter,
				outcome='bomb_ignore',
				p_k=self.bkt.get_knowledge(letter)
			)
	
	def on_missile_hit_ground(self, letter):
		self.bkt.update_incorrect(letter)
		if hasattr(self.gameplay, 'gameplay_logger'):
			self.gameplay.gameplay_logger.bkt_update(
				letter=letter,
				outcome='incorrect',
				p_k=self.bkt.get_knowledge(letter)
			)
	
	def get_bkt_state(self):
		"""Get current BKT state for all letters."""
		return self.bkt.get_all_knowledge()
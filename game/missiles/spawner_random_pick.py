# game/spawner/random_pick.py
import random
from game.missiles.missile_spawner import MissileSpawner

class RandomPickSpawner(MissileSpawner):
	def __init__(
		self,
		gameplay,
		available_letters,
		spawn_interval=5.0,
		speed_range=(10.0, 15.0),
		hint_range=(0.3, 0.7)
	):
		super().__init__(gameplay)

		self.available_letters = available_letters
		self.spawn_interval = spawn_interval
		self.speed_range = speed_range
		self.hint_range = hint_range

		self.timer = 0.0

	# --------------------------------------------------
	def update(self, dt):
		self.timer += dt

		if self.timer >= self.spawn_interval:
			self.timer -= self.spawn_interval
			self.spawn_random_missile()

	# --------------------------------------------------
	def spawn_random_missile(self):
		column = self.get_free_column()

		# get free letter among available letters and not currently active on a missile
		free_letters = self.get_free_letters()
		if free_letters is not None:
			free_letters = list(set(free_letters) & set(self.available_letters))
		letter = None
		if free_letters:
			letter = random.choice(free_letters)
		
		if column is None or letter is None:
			return  # no free column or letter available

		speed = random.uniform(*self.speed_range)
		hint_start = random.uniform(*self.hint_range)

		self.spawn_missile(
			column=column,
			letter=letter,
			speed=speed,
			hint_start=hint_start
		)
class Effect:
    def __init__(self, duration):
        self.duration = duration
        self.elapsed = 0.0
        self.alive = True

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.alive = False

    def draw(self, surface):
        pass

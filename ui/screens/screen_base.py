class Screen:
    def handle_event(self, event):
        pass
    def update(self, dt: float):
        pass
    def render(self, surface):
        raise NotImplementedError

"""Useful for mocking a config for testing"""

class FakeConfig:
    def __init__(self, config):
        self.config = config
    
    def section(self, name):
        return self.config[name]

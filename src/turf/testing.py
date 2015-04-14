"""Useful for mocking a config for testing"""

from unittest import mock

class FakeConfig:
    def __init__(self, config):
        self.config = config
    
    def section(self, name):
        return self.config[name]

def create_fake_config(config):
    fake_config = mock.MagicMock()
    fake_config._fake_config = FakeConfig(config)
    fake_config.section = fake_config._fake_config.section
    return fake_config



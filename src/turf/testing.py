"""Useful for mocking a config for testing"""

from unittest import mock

class FakeConfig:
    def __init__(self, config, raise_missing=False, missing_default=""):
        self.config = config
    
    def section(self, name):
        try:
            return self.config[name]
        except KeyError:
            if raise_missing:
                raise
            else:
               return missing_default

def create_fake_config(config):
    fake_config = mock.MagicMock()
    fake_config._fake_config = FakeConfig(config)
    fake_config.section = fake_config._fake_config.section
    return fake_config


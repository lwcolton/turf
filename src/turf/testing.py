"""Useful for mocking a config for testing"""

from unittest import mock

class FakeConfig:
    def __init__(self, config, raise_missing=False, missing_default=""):
        self.config = config
        self.raise_missing = raise_missing
        self.missing_default = missing_default
    
    def section(self, name):
        try:
            return self.config[name]
        except KeyError:
            if self.raise_missing:
                raise
            else:
                fake_dict = mock.MagicMock()
                fake_dict.__getitem__ = lambda x, y: self.missing_default
                return fake_dict

def create_fake_config(config):
    fake_config = mock.MagicMock()
    fake_config._fake_config = FakeConfig(config)
    fake_config.section = fake_config._fake_config.section
    return fake_config


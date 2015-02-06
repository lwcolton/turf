from unittest import mock

from turf.config import BaseConfig

class TestConfig:
    @mock.patch("turf.config.BaseConfig.read_section_from_file")
    def test_is_debug(self, read_section):
        read_section.return_value = {}
        assert not BaseConfig.is_debug()
        with mock.patch.dict("turf.config.BaseConfig.defaults", {"main":{"debug":True}}) as defaults_patch:
            BaseConfig.refresh()
            assert BaseConfig.is_debug()

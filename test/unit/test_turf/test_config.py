import random
from unittest import mock
import uuid

from nose2.tools import params

from turf.config import BaseConfig

def random_settings_dict():
    return {uuid.uuid4().hex:uuid.uuid4().hex for x in range(0,random.randrange(5,10))}

def random_settings_many():
    return [random_settings_dict() for x in range(0,6)]

class TestConfig:
    @mock.patch("turf.config.BaseConfig.read_section_from_file")
    def test_is_debug(self, read_section):
        read_section.return_value = {}
        assert not BaseConfig.is_debug()
        with mock.patch.dict("turf.config.BaseConfig.defaults", {"main":{"debug":True}}) as defaults_patch:
            BaseConfig.refresh()
            assert BaseConfig.is_debug()

    @params(*random_settings_many())
    def test_section(self, section_dict):
        section_name = uuid.uuid4().hex
        with mock.patch("turf.config.BaseConfig._cache", new=mock.PropertyMock(
                return_value = {section_name:section_dict})) as cache_mock:
            for setting_name, setting_value in section_dict.items():
                assert BaseConfig.section(section_name)[setting_name] == setting_value

    def test_section_refresh(self):
        with mock.patch("turf.config.BaseConfig._cache", new=mock.PropertyMock(
                return_value = {"fake_section":{}})) as cache_mock:
            with mock.patch("turf.config.BaseConfig.refresh") as refresh_patch:
                BaseConfig.section("fake_section")
                refresh_patch.assert_called_one_with()
            

    
        
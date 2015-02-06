import random
from unittest import mock
import uuid

import cerberus
from nose2.tools import params
from nose2.tools.such import helper as assert_helper

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
            
    def test_get_schema(self):
        fake_schema = uuid.uuid4().hex
        with mock.patch("turf.config.BaseConfig.schema", new=mock.PropertyMock(
                return_value = fake_schema)) as schema_mock:
            assert BaseConfig.get_schema() == fake_schema

    def test_get_defaults(self):
        fake_defaults = uuid.uuid4().hex
        with mock.patch("turf.config.BaseConfig.defaults", new=mock.PropertyMock(
                return_value = fake_defaults)) as defaults_mock:
            assert BaseConfig.get_defaults() == fake_defaults

    def test_get_config_dir(self):
        assert_helper.assertRaises(NotImplementedError, BaseConfig.get_config_dir) 
        with mock.patch("turf.config.BaseConfig.config_dir", new=mock.PropertyMock(
                return_value = "fake_config_dir")) as config_dir_mock:
            assert BaseConfig.get_config_dir() == "fake_config_dir"

    def test_refresh(self):
        section_name = uuid.uuid4().hex
        fake_key = uuid.uuid4().hex
        fake_schema = {fake_key:{"type":"string"}}
        fake_defaults = {uuid.uuid4().hex:4}
        with mock.patch("turf.config.BaseConfig.defaults", new=mock.PropertyMock(
                return_value = {section_name:fake_defaults})) as defaults_mock:
            with mock.patch("turf.config.BaseConfig.schema", new=mock.PropertyMock(
                    return_value = {section_name:fake_schema})) as schema_mock:
                with mock.patch("turf.config.BaseConfig.load_section") as load_section_mock:
                    fake_rv = uuid.uuid4().hex
                    load_section_mock.return_value = fake_rv
                    BaseConfig.refresh()
                    assert BaseConfig._cache[section_name] == fake_rv
                    assert load_section_mock.called_once_with(section_name, fake_defaults, fake_schema)

    def test_load_section_schema_error(self):
        section_name = uuid.uuid4().hex
        fake_default_key = uuid.uuid4().hex
        fake_defaults = {fake_default_key:4}
        assert_helper.assertRaises(
                cerberus.ValidationError, BaseConfig.load_section, 
                section_name, fake_defaults, {fake_default_key:{"type":"boolean"}})

    @mock.patch("turf.config.BaseConfig.read_section_from_file")
    def test_load_section_prehook(self, read_section_patch):
        read_section_patch.return_value = {}
        section_name = uuid.uuid4().hex
        fake_key = uuid.uuid4().hex
        fake_val = uuid.uuid4().hex
        fake_schema = {fake_key:{"type":"string"}}
        fake_hook = mock.MagicMock(return_value = {fake_key:fake_val})
        with mock.patch("turf.config.BaseConfig.prehooks", new=mock.PropertyMock(
                return_value={section_name:fake_hook})) as prehooks_patch:
            BaseConfig.load_section(section_name, {}, fake_schema)
            fake_hook.assert_called_once_with(section_name, {})


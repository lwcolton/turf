# flake8: noqa
from io import StringIO
import os
import random
from unittest import mock, TestCase
import uuid

from nose2.tools import params
from nose2.tools.such import helper as assert_helper

from turf.config import BaseConfig
from turf.errors import ValidationError, SectionNotFoundError

def random_settings_dict():
    return {uuid.uuid4().hex:uuid.uuid4().hex for x in range(0,random.randrange(5,10))}

def random_settings_many():
    return [random_settings_dict() for x in range(0,6)]

class TestConfig(TestCase):

    def tearDown(self):
        mock.patch.stopall()

    @params(*random_settings_many())
    def test_section(self, section_dict):
        section_name = uuid.uuid4().hex
        with mock.patch.object(BaseConfig, "refresh_section"):
            config = BaseConfig()
            mock.patch.object(config, "data", new={section_name:section_dict}).start()
            mock.patch.object(config, "schema", new={section_name:{}}).start()
            for setting_name, setting_value in section_dict.items():
                assert config.section(section_name)[setting_name] == setting_value

    def test_section_refresh(self):
        fake_schema = {"fake_section":{}}

        class TestConfigRefreshClass(BaseConfig):
            data={"fake_section":{}}
            schema = fake_schema
            refresh_section = mock.MagicMock()

        config = TestConfigRefreshClass()
        TestConfigRefreshClass.refresh_section.assert_called_once_with("fake_section", {})
        config.refresh_section = mock.MagicMock()
        try:
            config["fake_section"]
        except SectionNotFoundError:
            pass
        TestConfigRefreshClass.refresh_section.assert_called_once_with("fake_section", {})

    def test_get_schema(self):
        fake_schema = {}
        with mock.patch("turf.config.BaseConfig.schema", new=mock.PropertyMock(
                return_value = fake_schema)) as schema_mock:
            assert BaseConfig().get_schema() == fake_schema

    def test_get_defaults(self):
        fake_defaults = uuid.uuid4().hex
        with mock.patch("turf.config.BaseConfig.defaults", new=mock.PropertyMock(
                return_value = fake_defaults)) as defaults_mock:
            assert BaseConfig().get_defaults() == fake_defaults

    def test_get_config_dir(self):
        assert_helper.assertRaises(NotImplementedError, BaseConfig().get_config_dir)
        with mock.patch("turf.config.BaseConfig.config_dir", new=mock.PropertyMock(
                return_value = "fake_config_dir")) as config_dir_mock:
            assert BaseConfig().get_config_dir() == "fake_config_dir"

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
                    config = BaseConfig()
                    assert config.data[section_name] == fake_rv
                    assert load_section_mock.called_once_with(section_name, fake_defaults, fake_schema)

    def test_load_section_schema_error(self):
        section_name = uuid.uuid4().hex
        fake_default_key = uuid.uuid4().hex
        fake_defaults = {fake_default_key:4}
        assert_helper.assertRaises(
                ValidationError, BaseConfig().load_section,
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
            assert BaseConfig().load_section(section_name, {}, fake_schema) == {fake_key:fake_val}
            fake_hook.assert_called_once_with(section_name, {})

    @mock.patch("turf.config.BaseConfig.read_section_from_file")
    def test_load_section_mergehook(self, read_section_patch):
        read_section_patch.return_value = {}
        section_name = uuid.uuid4().hex
        fake_key = uuid.uuid4().hex
        fake_val = uuid.uuid4().hex
        fake_schema = {fake_key:{"type":"string"}}
        fake_hook = mock.MagicMock(return_value = {fake_key:fake_val})
        with mock.patch("turf.config.BaseConfig.mergehooks", new=mock.PropertyMock(
                return_value={section_name:fake_hook})) as mergehooks_patch:
            assert BaseConfig().load_section(section_name, {}, fake_schema) == {fake_key:fake_val}
            fake_hook.assert_called_once_with(section_name, {}, {})

    @mock.patch("turf.config.BaseConfig.read_section_from_file")
    def test_load_section_posthook(self, read_section_patch):
        read_section_patch.return_value = {}
        section_name = uuid.uuid4().hex
        fake_key = uuid.uuid4().hex
        fake_val = uuid.uuid4().hex
        fake_schema = {fake_key:{"type":"string"}}
        fake_hook = mock.MagicMock(return_value = {fake_key:fake_val})
        with mock.patch("turf.config.BaseConfig.posthooks", new=mock.PropertyMock(
                return_value={section_name:fake_hook})) as posthooks_patch:
            assert BaseConfig().load_section(section_name, {}, fake_schema) == {fake_key:fake_val}
            fake_hook.assert_called_once_with(section_name, {})

    @mock.patch("turf.config.BaseConfig.read_section_from_file")
    def test_load_section_default_merge(self, read_section_patch):
        section_name = uuid.uuid4().hex
        fake_key = uuid.uuid4().hex
        fake_val = uuid.uuid4().hex
        fake_schema = {fake_key:{"type":"string"}}
        defaults = {fake_key:"bad_val"}
        read_section_patch.return_value = {fake_key:fake_val}
        assert BaseConfig().load_section(section_name, defaults, fake_schema) == {fake_key:fake_val}

    def test_read_section(cls):
        fake_config_dir = os.path.join("/tmp", uuid.uuid4().hex)
        section_name = uuid.uuid4().hex
        config_path = os.path.join(fake_config_dir, "{0}.yml".format(section_name))
        fake_key = uuid.uuid4().hex
        fake_val = uuid.uuid4().hex
        fake_yml = "---\n{0}: {1}".format(fake_key, fake_val)

        with mock.patch("turf.config.BaseConfig.config_dir", new=mock.PropertyMock(
                return_value = fake_config_dir)) as config_dir_patch:
            with mock.patch("yaml.safe_load") as patch_yaml:
                patch_yaml.return_value = {fake_key:fake_val}

                with mock.patch("builtins.open") as patch_open:
                    patch_open.return_value = StringIO(fake_yml)

                    with mock.patch("os.path.exists") as exists_patch:
                        exists_patch.return_value = True

                        section_config = BaseConfig().read_section_from_file(section_name)
                        assert section_config == {fake_key:fake_val}
                        patch_open.assert_called_once_with(config_path)
                        patch_yaml.assert_called_once_with(patch_open.return_value)

    def test_get_file_path_for_section(self):
        fake_config_dir = os.path.join("/tmp", uuid.uuid4().hex)
        section_name = uuid.uuid4().hex
        config_path = os.path.join(fake_config_dir, "{0}.yml".format(section_name))

        with mock.patch("turf.config.BaseConfig.config_dir", new=mock.PropertyMock(
                return_value = fake_config_dir)) as config_dir_patch:
            assert BaseConfig().get_file_path_for_section(section_name) == config_path

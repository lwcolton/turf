# flake8: noqa

import os
import uuid

from unittest import mock, TestCase

from turf.config import SingleFileConfig


class TestConfig(TestCase):

    def tearDown(self):
        mock.patch.stopall()

    def test_get_config_search_path(self):
        fake_config_dir = os.path.join("/tmp", uuid.uuid4().hex)

        with mock.patch("turf.config.SingleFileConfig.refresh") as patch_refresh:
            sfc = SingleFileConfig(search_path=[fake_config_dir])
            assert sfc.get_config_search_path() == [fake_config_dir]

    def test_get_file_path(self):
        fake_config_dir = os.path.join("/tmp", uuid.uuid4().hex)
        fake_file_name = "{0}.yml".format(uuid.uuid4().hex)
        config_path = os.path.join(fake_config_dir, fake_file_name)

        with mock.patch("turf.config.SingleFileConfig.refresh") as patch_refresh:
            with mock.patch("os.path.exists") as exists_patch:
                exists_patch.return_value = True

                sfc = SingleFileConfig(search_path=[fake_config_dir],
                                       config_file=fake_file_name)
                assert sfc.get_file_path() == config_path

    def test_single_file_config_refresh(self):
        fake_config_dir = os.path.join("/tmp", uuid.uuid4().hex)
        fake_file_name = "{0}.yml".format(uuid.uuid4().hex)

        fake_section = uuid.uuid4().hex
        fake_key = uuid.uuid4().hex
        fake_val = uuid.uuid4().hex
        fake_config = {fake_section:{fake_key:fake_val}}

        class Config(SingleFileConfig):
            schema = {fake_section:{fake_key:{"type":"string"}}}

        with mock.patch("turf.config.SingleFileConfig.yaml_load") as patch_yaml:
            with mock.patch("os.path.exists") as exists_patch:
                patch_yaml.return_value = fake_config

                sfc = Config(search_path=[fake_config_dir],
                             config_file=fake_file_name)
                assert fake_section in sfc


    def test_single_file_config(self):
        fake_config_dir = os.path.join("/tmp", uuid.uuid4().hex)
        fake_file_name = "{0}.yml".format(uuid.uuid4().hex)

        fake_section = uuid.uuid4().hex
        fake_key = uuid.uuid4().hex
        fake_val = uuid.uuid4().hex
        fake_config = {fake_section:{fake_key:fake_val}}

        class Config(SingleFileConfig):
            schema = {fake_section:{fake_key:{"type":"string"}}}

        with mock.patch("turf.config.SingleFileConfig.yaml_load") as patch_yaml:
            with mock.patch("os.path.exists") as exists_patch:
                patch_yaml.return_value = fake_config

                sfc = Config(search_path=[fake_config_dir],
                             config_file=fake_file_name)
                assert sfc.read_section_from_file(fake_section) == fake_config[fake_section]

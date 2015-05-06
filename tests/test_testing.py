from unittest import TestCase

from turf.testing import create_fake_config

class TestTesting(TestCase):
    def test_fake_config(self):
        fake_config = create_fake_config({"fake_section":{"fake_key":"fake_val"}})
        self.assertEquals(fake_config.section("fake_section")["fake_key"], "fake_val")

    def test_fake_config_missing(self):
        fake_config = create_fake_config({})
        self.assertEquals(fake_config.section("not_real")["nope"], "")

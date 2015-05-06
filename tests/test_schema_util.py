from unittest import TestCase

import turf.schema_util as schema_util

class TestTesting(TestCase):
    def test_make_not_empty(self):
        fake_setting = {"type":"string"}
        new_setting = schema_util.make_not_empty(fake_setting)
        self.assertEquals(new_setting["empty"], False)
        self.assertEquals(new_setting["type"], "string")
        self.assertEquals(len(new_setting.keys()), 2)

    def test_make_required_full(self):
        fake_setting = {"type":"string"}
        new_setting = schema_util.make_required_full(fake_setting)
        self.assertEquals(new_setting["empty"], False)
        self.assertEquals(new_setting["required"], True)
        self.assertEquals(new_setting["type"], "string")
        self.assertEquals(len(new_setting.keys()), 3)

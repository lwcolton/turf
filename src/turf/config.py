import os
import sys

import yaml

class BaseConfig:
    cache = None

    @classmethod
    def is_debug(cls):
        return cls.section("main").get("debug", False)

    @classmethod
    def get_sections(cls):
        return {
            "main":{
                "debug":False
            }
        }

    @classmethod
    def config_dir(cls):
        raise NotImplementedError

    @classmethod
    def section(cls, section_name, refresh=False): 
        if refresh or cls.cache == None:
            cls.refresh()
        return cls.cache.get(section_name, {})
        
    @classmethod
    def refresh(cls):
        cls.cache = {}
        for section_name, section_defaults in cls.get_sections().items():
            cls.cache[section_name] = cls.load_section(section_name, section_defaults)

    @classmethod
    def get_prehooks(cls):
        return {}

    @classmethod
    def get_mergehooks(cls):
        return {}

    @classmethod
    def get_posthooks(cls):
        return {}

    @classmethod
    def load_section(cls, section_name, section_defaults):
        prehooks = cls.get_prehooks()
        mergehooks = cls.get_mergehooks()
        posthooks = cls.get_posthooks()

        if section_name in prehooks:
            section_defaults = prehooks[section_name](section_name, section_defaults)

        config_from_file = cls.read_section_from_file(section_name)

        if section_name in merge_hooks:
            section_config = mergehooks[section_name](section_name, section_defaults, config_from_file)
        else:
            section_config = dict(list(section_defaults.items()) + list(config_from_file.items()))

        if section_name in posthooks:
            section_config = posthooks[section_name](section_name, section_config)
        
        return section_config

    def read_section_from_file(section_name):
        config_path = os.path.join(cls.config_dir(), "%s.yml" % section_name)
        if os.path.exists(config_path):
            with open(config_path) as config_file_handle:
                return yaml.load(config_file_handle)
        else:
           return {}

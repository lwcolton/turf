import os
import sys

import yaml

class BaseConfig:
    cache = None

    @classmethod
    def is_debug(cls):
        """Returns True if the app is in debug mode, otherwise False"""
        return cls.section("main").get("debug", False)

    @classmethod
    def section(cls, section_name, refresh=False): 
        """Returns a section of the configuration.

        This is how other parts of the application will access the configuration.
        """
        if refresh or cls.cache == None:
            cls.refresh()
        return cls.cache.get(section_name, {})

    @classmethod
    def get_sections(cls):
        """Returns a dictionary containing defaults for each section.

        Override this in your subclass.

        Dictionary structure is like::
            {
                'section_name':{
                    'setting_key':'default_value'
                },
            }
        """
        return {
            "main":{
                "debug":False
            }
        }

    @classmethod
    def config_dir(cls):
        """This needs to return the directory where your config files are stored.

        Override this in your subclass.

        :rtype: str
        """
        raise NotImplementedError
        
    @classmethod
    def refresh(cls):
        """Reloads all values from the files on disk, refreshing the cache."""
        cls.cache = {}
        for section_name, section_defaults in cls.get_sections().items():
            cls.cache[section_name] = cls.load_section(section_name, section_defaults)

    @classmethod
    def get_prehooks(cls):
        """Returns a dictionary mapping section names to pre-hooks.

        Return structure is like::
            {
                'section_name':<prehook function>
            }
        """
        return {}

    @classmethod
    def prehook_interface(cls, section_name, section_defaults):
        """Defines the interface for pre-hooks.

        Pre-hooks allow you to dynamically add or modify settings to a 
            section's defaults.

        :param str section_name: The name of the section this prehook is 
            being called to populate. Useful if you are assigning the same 
            prehook to multiple sections.

        :param dict section_defaults: Dictionary of default settings for this
            section as returned by :meth:`get_sections`.
        
        :rtype: dict of default values for this section.
        """

    @classmethod
    def get_mergehooks(cls):
        """Returns a dictionary mapping section names to merge-hooks.

        Return structure is like::
            {
                'section_name':<mergehook function>
            }
        """
        return {}

    @classmethod
    def get_posthooks(cls):
        """Returns a dictionary mapping section names to post-hooks.

        Return structure is like::
            {
                'section_name':<prehook function>
            }
        """
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

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
        raise NotImplementedError

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
    def mergehook_interface(cls, section_name, section_defaults, config_from_file):
        """Defines the interface for merge-hooks.

        Merge-hooks merge default settings for a section with those from the config file.
        The default behavior with no merge hook defined for a section is to overwrite
        top level keys in the defaults with those from the config file.  If this behavior
        is undesirable, you can use a merge-hook to define a custom implementation.

        :param str section_name: The name of the section this mergehook is 
            being called to populate. Useful if you are assigning the same 
            mergehook to multiple sections.

        :param dict section_defaults: Dictionary of default settings for this
            section as returned by :meth:`get_sections`.

        :param dict config_from_file: Dictionary of settings for this section
            as defined in its config file.

        :rtype: dict of settings to use for this section.
        """
        raise NotImplementedError


    @classmethod
    def get_posthooks(cls):
        """Returns a dictionary mapping section names to post-hooks.

        Return structure is like::
            {
                'section_name':<posthook function>
            }
        """
        return {}

    @classmethod
    def posthook_interface(cls, section_name, section_config):
        """Defintes the interface for post-hooks.

        Post-hooks are called after a config section is loaded and are useful for 
        any modifications you might need to make after defaults have been
        merged into the config from the file.

        :param str section_name: The name of the section this posthook is 
            being called to populate. Useful if you are assigning the same 
            posthook to multiple sections.
        
        :param dict section_config: The configuration for this section.
        
        :rtype: dict of settings to use for this section.
        """ 
        raise NotImplementedError

    @classmethod
    def load_section(cls, section_name, section_defaults):
        """Handles loading section.

        Calls all hooks and implements default merge behavior if none is defined.

        :rtype: dict of settings for this section.
        """
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
        """Loads a section from its config file and parses the YAML."""
        config_path = os.path.join(cls.config_dir(), "%s.yml" % section_name)
        if os.path.exists(config_path):
            with open(config_path) as config_file_handle:
                return yaml.load(config_file_handle)
        else:
           return {}

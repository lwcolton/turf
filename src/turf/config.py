import os

import yaml
import cerberus

from .errors import SectionNotFoundError, ValidationError

class BaseConfig:
    """Provides a base class for a configuration manager.

    You can subclass this to gain all sorts of neat functionality,
    like merging of defaults and readiny YAML from config files.

    You are required to provide a schema for your configuration,
    either using :attr:`schema` or :meth:`get_schema`.  This
    should be a `cerberus schema <https://cerberus.readthedocs.org/en/latest/>`_.
    See :meth:`get_schema` for implementation details.
    """
    defaults = {
        "main":{
            "debug":False
        }
    }

    schema = {
        "main":{
            "debug":{
                "type":"boolean"
            }
        }
    }

    prehooks = {}
    mergehooks = {}
    posthooks = {}

    safe_load = True

    config_dir = None

    _cache = None


    @classmethod
    def is_debug(cls):
        """Returns True if the app is in debug mode, otherwise False"""
        return cls.section("main").get("debug", False)

    @classmethod
    def section(cls, section_name, refresh=False):
        """Returns a section of the configuration.

        This is how other parts of the application will access the configuration.

        Example::

            Config.section("my_section")["my_setting"]
        """
        if refresh or cls._cache == None:
            cls.refresh()
        try:
            return cls._cache[section_name]
        except KeyError:
            raise SectionNotFoundError(section_name)

    @classmethod
    def get_validator(cls, schema=None):
        """Returns a cerberus validator from the schema"""
        if schema is None:
            schema = cls.get_schema()

        return cerberus.Validator(schema)

    @classmethod
    def get_schema(cls):
        """Returns a dictionary of cerberus schema describing the structure of your config.

        The top level keys should be section names and their values should be cerberus schema.

        The structure is like::

            {
                "section_name":{
                    "field_name":{
                        "ceberus":"schema"
                    }
                }
             }

        Example::

            {
                "app":{
                    "mysetting":{
                        "type":"string"
                    }
                }
            }

        Given that schema, you would have a file called app.yml with a key mysetting set to a string.
        """
        return cls.schema

    @classmethod
    def get_defaults(cls):
        """Returns a dictionary containing defaults for each section.

        Without overriding, this will return :attr:`defaults`.

        Dictionary structure is like::

            {
                'section_name':{
                    'setting_key':'default_value'
                },
            }
        """
        return cls.defaults

    @classmethod
    def get_config_dir(cls):
        """This needs to return the directory where your config files are stored.

        Without overriding, this will return :attr:`config_dir`, which you must set.

        :rtype: str
        """
        if cls.config_dir == None:
            raise NotImplementedError("Must define config_dir")
        else:
            return cls.config_dir

    @classmethod
    def refresh(cls):
        """Reloads all values from the files on disk, refreshing the cache.

        It's usually a good idea to call this during application startup
        because it will validate the configuration against the schema.
        """
        cls._cache = {}
        defaults = cls.get_defaults()
        for section_name, section_schema in cls.get_schema().items():
            section_defaults = defaults.get(section_name, {})
            cls._cache[section_name] = cls.load_section(section_name, section_defaults, section_schema)

    @classmethod
    def get_prehooks(cls):
        """Returns a dictionary mapping section names to pre-hooks.

        Without overriding, this will return :attr:`prehooks`.

        Return structure is like::

            {
                'section_name':<prehook function>
            }
        """
        return cls.prehooks

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

        Without overriding, this will return :attr:`mergehooks`.

        Return structure is like::

            {
                'section_name':<mergehook function>
            }
        """
        return cls.mergehooks

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

        Without overriding, this will return :attr:`posthooks`.

        Return structure is like::

            {
                'section_name':<posthook function>
            }
        """
        return cls.posthooks

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
    def load_section(cls, section_name, section_defaults, section_schema):
        """Handles loading section.

        Calls all hooks and implements default merge behavior if none is defined.

        :rtype: dict of settings for this section.
        """
        prehooks = cls.get_prehooks()
        mergehooks = cls.get_mergehooks()
        posthooks = cls.get_posthooks()

        validator = cls.get_validator(section_schema)

        if not validator.validate(section_defaults, update=True):
            cls.raise_validation_error(section_name, validator.errors)

        if section_name in prehooks:
            section_defaults = prehooks[section_name](section_name, section_defaults)

        if not validator.validate(section_defaults, update=True):
            cls.raise_validation_error(section_name, validator.errors)

        config_from_file = cls.read_section_from_file(section_name)

        if section_name in mergehooks:
            section_config = mergehooks[section_name](section_name, section_defaults, config_from_file)
        else:
            section_config = dict(list(section_defaults.items()) + list(config_from_file.items()))

        if not validator.validate(section_config, update=True):
            cls.raise_validation_error(section_name, validator.errors)

        if section_name in posthooks:
            section_config = posthooks[section_name](section_name, section_config)

        if not validator.validate(section_config):
            cls.raise_validation_error(section_name, validator.errors)

        return section_config

    @classmethod
    def get_file_path_for_section(cls, section_name):
        return os.path.join(cls.get_config_dir(), "%s.yml" % section_name)

    @classmethod
    def yaml_load(cls, config_path):
        if config_path and os.path.exists(config_path):
            with open(config_path) as config_file_handle:
                if cls.safe_load:
                    return yaml.safe_load(config_file_handle)
                else:
                    return yaml.load(config_file_handle)
        else:
            return {}

    @classmethod
    def read_section_from_file(cls, section_name):
        """Loads a section from its config file and parses the YAML."""
        config_path = cls.get_file_path_for_section(section_name)
        return cls.yaml_load(config_path)

    @classmethod
    def raise_validation_error(cls, section, errors):
        message = "Errors validating section '{0}':\n\n{1}".format(section, errors)
        raise ValidationError(message, section, errors)


class SingleFileConfig(BaseConfig):
    config_file = None
    search_path = None
    _conf_cache = None

    @classmethod
    def get_config_search_path(cls):
        if cls.search_path is None:
            raise NotImplementedError("Must define search_path")
        else:
            return cls.search_path

    @classmethod
    def get_file_path(cls):
        if cls.config_file is None:
            raise NotImplementedError("Must define config_file")
        else:
            for path in cls.get_config_search_path():  # pylint: disable=not-an-iterable
                if os.path.exists(os.path.join(path, cls.config_file)):
                    return os.path.join(path, cls.config_file)

    @classmethod
    def refresh_conf_cache(cls):
        config_path = cls.get_file_path()
        cls._conf_cache = cls.yaml_load(config_path)

    @classmethod
    def refresh(cls):
        cls.refresh_conf_cache()

        cls._cache = {}
        defaults = cls.get_defaults()
        schema = cls.get_schema()

        keys = set(list(cls._conf_cache.keys()) + list(defaults.keys()))

        for section_name in keys:
            section_defaults = defaults.get(section_name, {})
            section_schema = schema[section_name]
            cls._cache[section_name] = cls.load_section(section_name, section_defaults, section_schema)

    @classmethod
    def read_section_from_file(cls, section_name):
        if cls._conf_cache is None:
            cls.refresh_conf_cache()
        return cls._conf_cache.get(section_name, {})

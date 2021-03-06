from collections import UserDict
import os
import time
import warnings

import yaml
import cerberus

from .errors import SectionNotFoundError, SchemaNotFoundError, ValidationError

class BaseConfig(UserDict):
    """Provides a base class for a configuration manager.

    You can subclass this to gain all sorts of neat functionality,
    like merging of defaults and readiny YAML from config files.

    You are required to provide a schema for your configuration,
    either using :attr:`schema` or :meth:`get_schema`.  This
    should be a `cerberus schema <https://cerberus.readthedocs.org/en/latest/>`_.
    See :meth:`get_schema` for implementation details.
    """
    defaults = {}

    schema = {}

    prehooks = {}
    mergehooks = {}
    posthooks = {}

    safe_load = True

    config_dir = None

    def __init__(self, *args, values=None, schema=None, defaults=None,
                 config_dir=None, refresh_seconds=60, **kwargs):
        """
        :param str refresh_seconds: The age of a section in seconds before
            it will be refreshed from the configuration upon access.
        """
        if values is None:
            values = {}
        values.update(kwargs)
        super().__init__(*args, **values)
        if schema is not None:
            self.schema = schema
        if defaults is not None:
            self.defaults.update(defaults)
        if config_dir is not None:
            self.config_dir = config_dir
        self.section = self.get_section
        self.refresh_seconds = refresh_seconds
        self.last_refresh_sections = {}
        self.refresh()

    @classmethod
    def section(cls, section_name, refresh=False):
        warnings.warn("Config without instantiation is deprecated", DeprecationWarning)
        config = cls()
        return config.section(section_name)

    def get_section(self, section_name):
        return self[section_name]

    def __getitem__(self, key):
        """Returns a section of the configuration.

        This is how other parts of the application will access the configuration.

        Example::

            config["my_section"]["my_setting"]
        """
        try:
            section_schema = self.get_schema()[key]
        except KeyError:
            raise SchemaNotFoundError(key) from KeyError
        last_refresh = self.last_refresh_sections.get(key)
        do_refresh=False
        if not last_refresh:
            do_refresh=True
        elif int(time.time()) - last_refresh > self.refresh_seconds:
            do_refresh=True

        if do_refresh:
            self.refresh_section(key, section_schema)

        try:
            return self.data[key]
        except KeyError:
            raise SectionNotFoundError(key) from KeyError

    def get_validator(self, schema=None):
        """Returns a cerberus validator from the schema"""
        if schema is None:
            schema = self.get_schema()

        return cerberus.Validator(schema)

    def get_schema(self):
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
        return self.schema

    def get_defaults(self):
        """Returns a dictionary containing defaults for each section.

        Without overriding, this will return :attr:`defaults`.

        Dictionary structure is like::

            {
                'section_name':{
                    'setting_key':'default_value'
                },
            }
        """
        return self.defaults

    def get_config_dir(self):
        """This needs to return the directory where your config files are stored.

        Without overriding, this will return :attr:`config_dir`, which you must set.

        :rtype: str
        """
        if self.config_dir == None:
            raise NotImplementedError("Must define config_dir")
        else:
            return self.config_dir

    def refresh(self):
        """Reloads all values from the files on disk, verifying the data against the schema.

        This will be called on creating of a Config.
        """
        self.data = {}
        for section_name, section_schema in self.get_schema().items():
            self.refresh_section(section_name, section_schema)


    def refresh_section(self, section_name, section_schema):
        defaults = self.get_defaults()
        section_defaults = defaults.get(section_name, {})
        self.data[section_name] = self.load_section(section_name, section_defaults, section_schema)
        self.last_refresh_sections[section_name] = int(time.time())

    def get_prehooks(self):
        """Returns a dictionary mapping section names to pre-hooks.

        Without overriding, this will return :attr:`prehooks`.

        Return structure is like::

            {
                'section_name':<prehook function>
            }
        """
        return self.prehooks


    def prehook_interface(self, section_name, section_defaults):
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


    def get_mergehooks(self):
        """Returns a dictionary mapping section names to merge-hooks.

        Without overriding, this will return :attr:`mergehooks`.

        Return structure is like::

            {
                'section_name':<mergehook function>
            }
        """
        return self.mergehooks


    def mergehook_interface(self, section_name, section_defaults, config_from_file):
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



    def get_posthooks(self):
        """Returns a dictionary mapping section names to post-hooks.

        Without overriding, this will return :attr:`posthooks`.

        Return structure is like::

            {
                'section_name':<posthook function>
            }
        """
        return self.posthooks


    def posthook_interface(self, section_name, section_config):
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


    def load_section(self, section_name, section_defaults, section_schema):
        """Handles loading section.

        Calls all hooks and implements default merge behavior if none is defined.

        :rtype: dict of settings for this section.
        """
        prehooks = self.get_prehooks()
        mergehooks = self.get_mergehooks()
        posthooks = self.get_posthooks()

        validator = self.get_validator(section_schema)

        if not validator.validate(section_defaults, update=True):
            self.raise_validation_error(section_name, validator.errors)

        if section_name in prehooks:
            section_defaults = prehooks[section_name](section_name, section_defaults)

        if not validator.validate(section_defaults, update=True):
            self.raise_validation_error(section_name, validator.errors)

        config_from_file = self.read_section_from_file(section_name)

        if section_name in mergehooks:
            section_config = mergehooks[section_name](section_name, section_defaults, config_from_file)
        else:
            section_config = dict(list(section_defaults.items()) + list(config_from_file.items()))

        if not validator.validate(section_config, update=True):
            self.raise_validation_error(section_name, validator.errors)

        if section_name in posthooks:
            section_config = posthooks[section_name](section_name, section_config)

        if not validator.validate(section_config):
            self.raise_validation_error(section_name, validator.errors)

        return section_config


    def get_file_path_for_section(self, section_name):
        return os.path.join(self.get_config_dir(), "%s.yml" % section_name)

    def yaml_load(self, config_path):
        with open(config_path) as config_file_handle:
            if self.safe_load:
                return yaml.safe_load(config_file_handle)
            else:
                return yaml.load(config_file_handle)


    def read_section_from_file(self, section_name):
        """Loads a section from its config file and parses the YAML."""
        config_path = self.get_file_path_for_section(section_name)
        if os.path.exists(config_path):
            return self.yaml_load(config_path)
        else:
            return {}

    def raise_validation_error(self, section, errors):
        message = "Errors validating section '{0}':\n\n{1}".format(section, errors)
        raise ValidationError(message, section, errors)

class SingleFileConfig(BaseConfig):
    config_file = None
    search_path = None
    data = None
    file_data = None

    def __init__(self, *args, search_path=None, config_file=None, **kwargs):
        if search_path:
            self.search_path = search_path
        if config_file:
            self.config_file = config_file
        super().__init__(*args, **kwargs)

    def get_config_search_path(self):
        if self.search_path is None:
            raise NotImplementedError("Must define search_path")
        else:
            return self.search_path

    def get_file_path(self):
        if self.config_file is None:
            raise NotImplementedError("Must define config_file")
        else:
            for path in self.get_config_search_path():  # pylint: disable=not-an-iterable
                if os.path.exists(os.path.join(path, self.config_file)):
                    return os.path.join(path, self.config_file)

    def refresh(self):
        config_path = self.get_file_path()
        if config_path and os.path.exists(config_path):
            self.data = self.yaml_load(config_path)
        else:
            self.data = {}
        defaults = self.get_defaults()
        schema = self.get_schema()

        keys = set(list(self.data.keys()) + list(defaults.keys()))

        for section_name in keys:
            section_defaults = defaults.get(section_name, {})
            section_schema = schema[section_name]
            self.data[section_name] = self.load_section(section_name, section_defaults, section_schema)

    def read_section_from_file(self, section_name):
        return self.data.get(section_name, {})

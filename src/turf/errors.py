class SectionNotFoundError(Exception): pass

class SchemaNotFoundError(Exception): pass

class ConfigurationNotFoundError(Exception): pass

class ValidationError(Exception):
    def __init__(self, msg, section, errors):
        super().__init__(msg)
        self.section = section
        self.errors = errors

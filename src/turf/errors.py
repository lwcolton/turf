class SectionNotFoundError(BaseException): pass

class ValidationError(BaseException):
    def __init__(self, msg, section, errors):
        super().__init__(msg)
        self.section = section
        self.errors = errors

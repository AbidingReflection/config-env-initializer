class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors  # this is the list
        super().__init__("Validation failed with the following issues:")

    def __str__(self):
        return self.args[0] + "\n" + "\n".join(self.errors)

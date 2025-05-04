
class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        message = "\n\n".join(errors)
        super().__init__(f"Validation failed with the following issues:\n\n{message}")

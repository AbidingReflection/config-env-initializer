class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors  # List of validation issues
        super().__init__("Validation failed with the following issues:")

    def __str__(self):
        bullet_list = "\n".join(f"  - {e}" for e in self.errors)
        return f"{self.args[0]}\n{bullet_list}"

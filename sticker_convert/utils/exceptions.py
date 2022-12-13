class NoTokenException(Exception):
    def __init__(self, message="Token missing"):
        self.message = message
        super().__init__(self.message)
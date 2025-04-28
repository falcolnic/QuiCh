class CookieNotFoundException(Exception):
    def __init__(self):
        super().__init__("Cookie not found in the request.")


class InvalidPasswordException(Exception):
    def __init__(self):
        super().__init__("Invalid password.")


class InvalidUsernameException(Exception):
    def __init__(self):
        super().__init__("Invalid username.")


class InvalidCredentialsException(Exception):
    def __init__(self):
        super().__init__("Invalid credentials.")


class DuplicateUsernameException(Exception):
    def __init__(self):
        super().__init__("Username already exists.")


class DuplicateEmailException(Exception):
    def __init__(self):
        super().__init__("Email already exists.")


class TokenValidationException(Exception):
    def __init__(self):
        super().__init__("Token validation failed.")


class UserNotFoundException(Exception):
    def __init__(self):
        super().__init__("User not found.")

from django.core.exceptions import ValidationError
import re

class ComplexPasswordValidator:
    """
    Validate whether the password contains at least one uppercase letter,
    at least one digit, and at least one special character.
    """
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "This password must contain at least one uppercase letter.",
                code='password_no_upper',
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                "This password must contain at least one digit.",
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*()_+\-=]', password):
            raise ValidationError(
                "This password must contain at least one special character.",
                code='password_no_special',
            )

    def get_help_text(self):
        return "Your password must contain at least 1 uppercase letter, 1 digit, and 1 special character."

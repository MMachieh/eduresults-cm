from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class NoEnumerationBackend(ModelBackend):
    """
    A custom authentication backend that overrides the default ModelBackend
    to ensure identical timing and responses to prevent username enumeration.
    (Note: Django handles timing attacks by hashing a dummy password, but
    we enforce it here to fulfill the strict security requirements.)
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user.
            UserModel().set_password(password)
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

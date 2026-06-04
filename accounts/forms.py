from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Student
import re

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': "Invalid username or password.",
        'inactive': "This account is inactive.",
    }

class ParentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    student_matricule = forms.CharField(max_length=20, required=True, label="Child's Matricule Number", help_text="Enter the official matricule number of your child.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'student_matricule')

    def clean_student_matricule(self):
        matricule = self.cleaned_data.get('student_matricule')
        return matricule

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Strip spaces
            phone_number = phone_number.replace(' ', '')
            if not re.match(r'^\+?[0-9]{9,15}$', phone_number):
                raise forms.ValidationError("Enter a valid phone number (e.g. +237612345678).")
        return phone_number

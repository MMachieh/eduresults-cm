from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Student

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
        try:
            student = Student.objects.get(matricule=matricule)
        except Student.DoesNotExist:
            raise forms.ValidationError("No student found with this matricule number. Please check and try again.")
        return matricule

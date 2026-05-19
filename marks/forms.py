from django import forms
from django.core.exceptions import ValidationError
from .models import Mark

class MarkEntryForm(forms.ModelForm):
    class Meta:
        model = Mark
        fields = ['value', 'remark']
        widgets = {
            'value': forms.NumberInput(attrs={
                'step': '0.25', 
                'min': '0', 
                'max': '20', 
                'class': 'form-control',
                'placeholder': 'AB'
            }),
            'remark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional remark'}),
        }
    
    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value is not None:
            if value < 0 or value > 20:
                raise ValidationError("Mark must be between 0 and 20.")
        return value

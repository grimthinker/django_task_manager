
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.admin import widgets
from ajax_select.fields import AutoCompleteSelectMultipleField

from .models import*

COLORS = {
        'disabled': 'rgb({}, {}, {})'.format(236,240,243),
        'enabled': 'rgb({}, {}, {})'.format(255,255,255),
        }


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['name', 'second_name' ,'middle_name', 'department']


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'body', 'responsible_users', 'justification', 'comment',]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'responsible_users': forms.SelectMultiple(attrs={'class':'form-select', 'size':8, 'style':'background-color: {};'.format(COLORS['enabled'])}),
            'body': forms.Textarea(attrs={'class':'form-control', "rows":9, "cols":24}),
            'justification': forms.Textarea(attrs={'class':'form-control', "rows":2, "cols":24}),
            'comment': forms.Textarea(attrs={'class':'form-control', "rows":3, "cols":24}),
        }




class DepartmentForm(forms.ModelForm):
    workers = forms.ModelMultipleChoiceField(queryset=UserProfile.objects.all(), required = False, widget=forms.SelectMultiple(attrs={'class':'form-select'}))
    class Meta:
        model = Department
        fields = ['name', 'body', 'chief', 'workers', 'super_department',]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class':'form-control', "rows":6, "cols":24, 'style':'background-color: {};'.format(COLORS['enabled'])}),
            'chief': forms.Select(attrs={'class': 'form-select'}),
            'workers': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'super_department': forms.Select(attrs={'class': 'form-select'}),
        }

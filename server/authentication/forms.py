from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class CreateUserForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control bg-white rounded shadow-sm'}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control  bg-white rounded shadow-sm'}))
    password1 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control  bg-white rounded shadow-sm', 'id': 'registerInput'}))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control  bg-white rounded shadow-sm', 'id': 'inputRegistertwo'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

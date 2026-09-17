from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from datetime import date
from django.db.models import Q
from django.urls import reverse

from .models import *

# Extended Models
from client.models import *

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
# email imports start
from django.core.mail import send_mail
from django.conf import settings
# email imports end

# Authentication Imports start
from .forms import CreateUserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user, allowed_user
from django.contrib.auth.models import Group
# Authentication Imports end


# Invite user password
from django.contrib.auth.forms import SetPasswordForm

# Create your views here.


@unauthenticated_user
def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user = request.user
            current_user = UserModel.objects.get(user=user)
            if current_user.account_complete == False:
                return redirect('account:account-setup')
            else:
                return redirect('dashboard:todays-work')
        else:
            messages.success(request, '❌ Username or Password is incorrect')

    return render(request, "authentication/login.html")


@unauthenticated_user
def RegisterUser(request):
    form = CreateUserForm()
    if request.method == 'POST' and 'create-account' in request.POST:
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            user_email = form.cleaned_data.get('email')

            UserModel.objects.create(
                user=user,
                first_name=username,
                email=user_email,
                agreeTerms=True,
            )

            messages.success(request, 'Account was created for ' + username)
            return redirect("login")

    context = {
        'form': form
    }
    return render(request, "authentication/register.html", context)


# logout user
def LogoutUser(request):
    logout(request)
    return redirect('login')

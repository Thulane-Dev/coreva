
from django.urls import path
from .import views

app_name = "account"

urlpatterns = [
    path('account', views.AccountView, name='account'),
    path('account-setup', views.AccountSetupView, name='account-setup'),
    path('save-account-setup', views.save_account_setup, name='save-account-setup'),
]


from django.urls import path
from .import views

app_name = "dashboard"

urlpatterns = [
    path('todays-work', views.TodaysDashboardView, name='todays-work'),
    path('today', views.TodaysDashboardViewNew, name='today'),
]





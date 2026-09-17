from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone


# Models Import
from authentication.models import UserModel
from account.models import *
from projects.models import *
from inspections.models import *


# Services Import
from .services.dashboard_view import (
    get_all_projects_data
)


# ============= Todays Dashboard =============
def TodaysDashboardView(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    today = timezone.now()
    user_projects = ProjectUserModel.objects.filter(project_user=current_user)
    projects_data = get_all_projects_data(
        company=company, current_user=current_user)
    total_projects = projects_data['total_projects']
    projects = projects_data['projects_list']

    context = {
        "current_user": current_user,
        "today": today,
        "user_projects": user_projects,
        "projects_data": projects_data,
        "projects": projects,
        "total_projects": total_projects,
        "page": "dashboard/dashboard.html",
    }

    if request.htmx:
        return render(request, "dashboard/dashboard.html", context)
    return render(request, "client/base.html", context)


# ============= Todays Dashboard New =============
def TodaysDashboardViewNew(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    today = timezone.now()
    user_projects = ProjectUserModel.objects.filter(project_user=current_user)
    projects_data = get_all_projects_data(
        company=company, current_user=current_user)
    total_projects = projects_data['total_projects']
    projects = projects_data['projects_list']

    context = {
        "current_user": current_user,
        "today": today,
        "user_projects": user_projects,
        "projects_data": projects_data,
        "projects": projects,
        "total_projects": total_projects,
        "page": "dashboard/todays_page.html",
    }

    if request.htmx:
        return render(request, "dashboard/todays_page.html", context)
    return render(request, "client/base.html", context)

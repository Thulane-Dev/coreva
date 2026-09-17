from django.apps import apps
from datetime import date
from django.db.models import Q
from itertools import groupby
from django.utils import timezone
from datetime import timedelta


# Services Import
from projects.services.projects_view import (
    get_project_data
)


# Models import
ProjectModel = apps.get_model(
    "projects", "ProjectModel")


def get_all_projects_data(
        company,
        current_user=None,
):
    projects_list = []
    needs_attention_projects = 0

    projects = ProjectModel.objects.filter(
        company=company).order_by('created_at')

    for data in projects:
        project_data = get_project_data(
            project=data, current_user=current_user)

        # Create project Object
        project_object = {
            "project": data,
            "project_data": project_data,
            "project_status": data.status,
            "overall_status": project_data['overall_status'],
            "inspection_status": project_data['inspection_status']
        }

        projects_list.append(project_object)

    for data in projects_list:
        if data['overall_status'] == 'Needs Attention':
            needs_attention_projects += 1

    return {
        "projects_list": projects_list,
        "total_projects": projects.count(),
        "needs_attention_projects": needs_attention_projects,
    }

from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

# htmx
from django.http import HttpResponse
import json


# Create your views here.
# Models Import
from .models import *
from authentication.models import *
from account.models import AddressModel
from projects.models import *


# ============= Incidents View =============
def IncidentsView(request):

    context = {
        "page": "incidents/incidents.html",
    }

    if request.htmx:
        return render(request, "incidents/incidents.html", context)
    return render(request, "client/base.html", context)


# ============= LOG INCIDENT =============
def LogIncidentView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    context = {
        "current_user": current_user,
        "project": project,
        "today": today,
        "page": "incidents/log_incident.html",
    }

    if request.htmx:
        return render(request, "incidents/log_incident.html", context)
    return render(request, "client/base.html", context)


# ============= SAVE NEW INCIDENT POST METHOD =============
def save_new_incident(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    if request.method == "POST":
        # =============== CREATE INCIDENT ===============
        incident = IncidentModel.objects.create(
            project=project,
            incident_date=request.POST.get("incident_date"),
            incident_time=request.POST.get("incident_time"),
            title=request.POST.get("title"),
            work=request.POST.get("activity"),
            description=request.POST.get("description"),
            action_taken=request.POST.get("immediate_action"),
            severity=request.POST.get("severity"),
            incident_type=request.POST.get("incident_type"),
            weather_conditions=request.POST.get("weather_condition"),
            location=request.POST.get("location"),
            created_by=current_user,
        )

        # =============== INJURED PERSONS ===============
        first_names = request.POST.getlist("injured_first_name[]")
        last_names = request.POST.getlist("injured_last_name[]")
        injuries = request.POST.getlist("injured_injury[]")
        body_parts = request.POST.getlist("injured_body_part[]")
        treatments = request.POST.getlist("injured_treatment[]")

        for first_name, last_name, injury, body_part, treatment in zip(
            first_names,
            last_names,
            injuries,
            body_parts,
            treatments,
        ):
            InjuredPersonModel.objects.create(
                incident=incident,
                first_name=first_name,
                last_name=last_name,
                injury=injury,
                body_part=body_part,
                treatment=treatment,
            )

        # =============== WITNESS ===============
        witness_names = request.POST.getlist("witness_name[]")
        witness_contacts = request.POST.getlist("witness_contact[]")
        for name, contact in zip(
            witness_names,
            witness_contacts
        ):
            WitnessModel.objects.create(
                incident=incident,
                full_name=name,
                contract=contact,
            )

        # =============== FILES ===============
        attachments = request.FILES.getlist("attachments")
        for attachment in attachments:
            ProjectImages.objects.create(
                incident=incident,
                caption=incident.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )

        # =============== CREATE PROJECT TIMELINE ===============
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Incident Logged',
            description=f'{current_user.first_name} {current_user.last_name} logged an incident - {incident.incident_type}',
            icon_type='incident',
        )

        url = reverse(
            "projects:project-view",
            kwargs={"project_uuid": project.uuid}
        )

        response = HttpResponse(status=200)

        response["HX-Location"] = json.dumps({
            "path": f"{url}#incident{incident.id}",
            "target": "#content",
            "swap": "innerHTML",
        })

        return response


# ============= Project Incidents =============
def ProjectIncidentsPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    incidents = IncidentModel.objects.filter(
        Q(project=project)).order_by('-created_at')

    context = {
        "current_user": current_user,
        "project": project,
        "incidents": incidents,
        "page": "incidents/project_incidents.html",
    }

    if request.htmx:
        return render(request, "incidents/project_incidents.html", context)
    return render(request, "client/base.html", context)

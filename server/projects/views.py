from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
import requests
from django.db.models import Q
from itertools import groupby

# htmx
from django.http import HttpResponse
import json

# Models Import
from .models import *
from authentication.models import *
from account.models import AddressModel
from incidents.models import *

# Services Import
from .services.projects_view import (
    get_project_data
)


# ============= Projects View =============
def ProjectsView(request):

    context = {
        "page": "projects/projects.html",
    }

    if request.htmx:
        return render(request, "projects/projects.html", context)
    return render(request, "client/base.html", context)


# ============= Add Project =============
def AddProjectView(request):
    work_days = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
        ("sunday", "Sunday"),
    ]

    context = {
        "work_days": work_days,
        "page": "projects/add_project.html",
    }

    if request.htmx:
        return render(request, "projects/add_project.html", context)
    return render(request, "client/base.html", context)


# ============= Save New Project Post =============
@require_POST
def save_new_project(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    # =============== check if estimate date is selected  ===============
    end_date_estimate = request.POST.get("end_date")
    if end_date_estimate:
        end_date = request.POST.get("end_date")
    else:
        end_date = None

    # =============== check if cover image is added ===============
    cover_image = request.FILES.get("cover_image")
    if cover_image:
        project_image = request.FILES.get("cover_image")
    else:
        project_image = None

    # =============== Save Location ===============
    project_location = AddressModel.objects.create(
        street_address=request.POST.get("street_address"),
        city=request.POST.get("city"),
        province=request.POST.get("province"),
        postal_code=request.POST.get("postal_code"),
        country=request.POST.get("country"),
    )

    # =============== Save Project Object ===============
    project = ProjectModel.objects.create(
        company=company,
        created_by=current_user,
        project_name=request.POST.get("project_name"),
        start_date=request.POST.get("start_date"),
        end_date=end_date,
        location=project_location,
        cover_image=project_image,
        latitude=request.POST.get("latitude"),
        longitude=request.POST.get("longitude"),
    )

    # =============== Save Project User ===============
    ProjectUserModel.objects.create(
        project=project,
        project_user=current_user,
        added_by=current_user,
    )

    messages.success(
        request,
        f"✅ {project.project_name} added successfully."
    )

    # 🎯 Redirect To Projects
    url = reverse('dashboard:today')
    return redirect(f"{url}#project-{project.id}")


# ============= Weather Function =============
def get_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()

    return response.json()


# ============= Project Details =============
def ProjectDetailsView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    project_data = get_project_data(project=project, current_user=current_user)
    today = timezone.now().date()
    incidents = project_data['incidents']
    incidents_count = incidents.count()
    deliveries = project_data['deliveries']
    deliveries_count = deliveries.count()
    project_activity = project_data['grouped_activities']

    context = {
        "current_user": current_user,
        "project": project,
        "project_data": project_data,
        "today": today,
        "incidents": incidents,
        "incidents_count": incidents_count,
        "deliveries": deliveries,
        "deliveries_count": deliveries_count,
        "project_activity": project_activity,
        "page": "projects/project_details.html",
    }

    if request.htmx:
        return render(request, "projects/project_details.html", context)
    return render(request, "client/base.html", context)


# ============= New Project Details =============
def NewProjectDetailsView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    project_data = get_project_data(project=project, current_user=current_user)
    today = timezone.now().date()
    incidents = project_data['incidents']
    incidents_count = incidents.count()
    deliveries = project_data['deliveries']
    deliveries_count = deliveries.count()
    project_activity = project_data['grouped_activities']

    context = {
        "current_user": current_user,
        "project": project,
        "project_data": project_data,
        "today": today,
        "incidents": incidents,
        "incidents_count": incidents_count,
        "deliveries": deliveries,
        "deliveries_count": deliveries_count,
        "project_activity": project_activity,
        "page": "projects/new_project_details.html",
    }

    if request.htmx:
        return render(request, "projects/new_project_details.html", context)
    return render(request, "client/base.html", context)


# ============= Add Project Incident =============
def add_project_incident(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

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

    incidents = IncidentModel.objects.filter(
        Q(project=project) & Q(incident_date=today)).order_by('-created_at')[:4]
    incidents_count = incidents.count()

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Incident Logged',
        description=f'{current_user.first_name} {current_user.last_name} logged an incident - {incident.incident_type}',
        icon_type='incident',
    )

    return render(
        request,
        "partials/project_incidents_response.html",
        {
            "incidents": incidents,
            "incidents_count": incidents_count,
        },
    )


# ============= Add Project Delivery  DELETE =============
def add_project_delivery(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    if request.method == 'POST' and 'submit_delivery_lg' in request.POST:
        screen_display = 'LARGE SCREEN'

    if request.method == 'POST' and 'submit_delivery_sm' in request.POST:
        screen_display = 'SMALL SCREEN'

    delivery = DeliveryModel.objects.create(
        project=project,
        delivery_date=request.POST.get("delivery_date"),
        delivery_time=request.POST.get("delivery_time"),
        supplier=request.POST.get("supplier"),
        notes=request.POST.get("notes"),
        status=request.POST.get("status"),
        created_by=current_user,
    )

    # =============== DELIVERIES ITEMS ===============
    delivery_items = request.POST.getlist("delivery_item[]")
    delivery_quantities = request.POST.getlist("delivery_quantity[]")
    delivery_units = request.POST.getlist("delivery_unit[]")

    for item, quantity, unit in zip(
        delivery_items,
        delivery_quantities,
        delivery_units,
    ):
        DeliveredItemsModel.objects.create(
            delivery=delivery,
            item=item,
            quantity=quantity,
            unit=unit,
        )

    # =============== FILES ===============
    attachments = request.FILES.getlist("attachments")
    for attachment in attachments:
        ProjectImages.objects.create(
            project=project,
            delivery=delivery,
            caption=delivery.reference,
            photo=attachment,
            uploaded_by_user=current_user,
        )

    deliveries = DeliveryModel.objects.filter(
        Q(project=project) & Q(delivery_date=today)).order_by('-created_at')

    deliveries_count = deliveries.count()

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Delivery Created',
        description=f'{current_user.first_name} {current_user.last_name} added a delivery - {delivery.reference}',
        icon_type='delivery',
    )

    # 🎯 Redirect To Projects
    url = reverse('projects:project-view', args=[project.uuid, ])
    return redirect(f"{url}#Deliveries")

# =================================================================================================


# ============= NEW PROJECT PREVIEW DETAILS =============
def ProjectDetailsPreviewDetails(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    project_data = get_project_data(project=project, current_user=current_user)
    today = timezone.now().date()
    incidents = project_data['incidents']
    incidents_count = incidents.count()
    deliveries = project_data['deliveries']
    deliveries_count = deliveries.count()
    project_activity = project_data['grouped_activities']

    context = {
        "current_user": current_user,
        "project": project,
        "project_data": project_data,
        "today": today,
        "incidents": incidents,
        "incidents_count": incidents_count,
        "deliveries": deliveries,
        "deliveries_count": deliveries_count,
        "project_activity": project_activity,
        "page": "projects/project_preview_details.html",
    }

    if request.htmx:
        return render(request, "projects/project_preview_details.html", context)
    return render(request, "client/base.html", context)


# ============= ADD PROJECT DELIVERY  =============
def LogProjectDeliveryView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    context = {
        "current_user": current_user,
        "project": project,
        "today": today,
        "page": "projects/log_project_delivery.html",
    }

    if request.htmx:
        return render(request, "projects/log_project_delivery.html", context)
    return render(request, "client/base.html", context)


# ============= SAVE NEW DELIVERY POST METHOD =============
def save_new_delivery(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    if request.method == "POST":
        # Create Delivery Object
        delivery = DeliveryModel.objects.create(
            project=project,
            delivery_date=request.POST.get("delivery_date"),
            delivery_time=request.POST.get("delivery_time"),
            supplier=request.POST.get("supplier"),
            notes=request.POST.get("notes"),
            status=request.POST.get("status"),
            created_by=current_user,
        )

        # =============== DELIVERIES ITEMS ===============
        delivery_items = request.POST.getlist("delivery_item[]")
        delivery_quantities = request.POST.getlist("delivery_quantity[]")
        delivery_units = request.POST.getlist("delivery_unit[]")

        for item, quantity, unit in zip(
            delivery_items,
            delivery_quantities,
            delivery_units,
        ):
            DeliveredItemsModel.objects.create(
                delivery=delivery,
                item=item,
                quantity=quantity,
                unit=unit,
            )

        # =============== FILES ===============
        attachments = request.FILES.getlist("attachments")
        for attachment in attachments:
            ProjectUploadedFiles.objects.create(
                project=project,
                delivery=delivery,
                caption=delivery.reference,
                photo=attachment,
                uploaded_by_user=current_user,
            )

        # =============== CREATE PROJECT TIMELINE ===============
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Delivery Created',
            description=f'{current_user.first_name} {current_user.last_name} added a delivery - {delivery.reference}',
            icon_type='delivery',
        )

        # 🎯 Redirect To Projects
        url = reverse('projects:project-view', args=[project.uuid, ])
        return redirect(f"{url}#Deliveries")


# ============= Project Deliveries =============
def ProjectDeliveriesPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    # ==================================================
    # Deliveries
    # ==================================================
    deliveries = DeliveryModel.objects.filter(
        Q(project=project)).order_by('-created_at')

    context = {
        "current_user": current_user,
        "project": project,
        "deliveries": deliveries,
        "page": "projects/project_deliveries.html",
    }

    if request.htmx:
        return render(request, "projects/project_deliveries.html", context)
    return render(request, "client/base.html", context)


# ============= Project Activity =============
def ProjectActivityDetailsPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    activities = ActivityModel.objects.filter(
        Q(project=project)).order_by('-created_at')

    grouped_activities = []

    for index, (date, activities_on_date) in enumerate(
        groupby(
            activities,
            key=lambda activity: timezone.localtime(activity.created_at).date()
        ),
        start=1
    ):
        grouped_activities.append({
            "id": index,
            "date": date,
            "activities": list(activities_on_date),
        })

    context = {
        "current_user": current_user,
        "project": project,
        "project_activity": grouped_activities,
        "page": "projects/project_activity.html",
    }

    if request.htmx:
        return render(request, "projects/project_activity.html", context)
    return render(request, "client/base.html", context)

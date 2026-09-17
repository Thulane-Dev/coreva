from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
import requests


# Models Import
from .models import *
from projects.models import *
from authentication.models import *
from issues.models import *
from incidents.models import *

# Services Import
from .services.report_view import (
    get_daily_report,
    get_missed_report_days
)


# ============= Weather Function =============
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",

    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",

    45: "Fog",
    48: "Depositing rime fog",

    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",

    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",

    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",

    66: "Light freezing rain",
    67: "Heavy freezing rain",

    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",

    77: "Snow grains",

    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",

    85: "Slight snow showers",
    86: "Heavy snow showers",

    95: "Thunderstorm",

    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_weather_condition(code):
    return WEATHER_CODES.get(
        code,
        "Unknown"
    )


def get_weather(latitude, longitude):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "weather_code"
        ),

        "daily": (
            "weather_code,"
            "temperature_2m_min,"
            "temperature_2m_max,"
            "precipitation_probability_max,"
            "precipitation_sum"
        ),

        "timezone": "auto",
    }

    response = requests.get(
        WEATHER_API_URL,
        params=params,
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


def get_daily_report_weather(latitude, longitude):

    weather = get_weather(
        latitude,
        longitude,
    )

    current = weather.get(
        "current",
        {}
    )

    daily = weather.get(
        "daily",
        {}
    )

    weather_code = current.get(
        "weather_code"
    )

    return {
        "condition": get_weather_condition(
            weather_code
        ),

        "temperature": current.get(
            "temperature_2m"
        ),

        "min_temperature": (
            daily
            .get("temperature_2m_min", [None])[0]
        ),

        "max_temperature": (
            daily
            .get("temperature_2m_max", [None])[0]
        ),

        "rain_probability": (
            daily
            .get(
                "precipitation_probability_max",
                [None]
            )[0]
        ),

        "rainfall": (
            daily
            .get("precipitation_sum", [None])[0]
        ),

        "wind_speed": current.get(
            "wind_speed_10m"
        ),

        "humidity": current.get(
            "relative_humidity_2m"
        ),
    }


# ============= Report View =============
def ReportView(request):

    context = {
        "page": "report/report_view.html",
    }

    if request.htmx:
        return render(request, "report/report_view.html", context)
    return render(request, "client/base.html", context)


# ============= Create Report =============
def CreateReportView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    contractors = ProjectContractor.objects.filter(
        project=project).order_by('-created_at')
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()
    tomorrow = timezone.now().date() + timedelta(days=1)
    report_data = get_daily_report(project=project, current_user=current_user)
    report = report_data['report']
    tasks = report_data['tasks'][:4]
    all_tasks = report_data['tasks']
    future_tasks = report_data['future_tasks'][:4]
    all_future_tasks = report_data['future_tasks']
    all_issues = report_data['issues']
    issues = report_data['issues'][:4]
    all_deliveries = report_data['deliveries']
    deliveries = report_data['deliveries'][:4]
    all_incidents = report_data['incidents']
    incidents = report_data['incidents'][:4]
    files = report_data['files']

    # weather = None
    # if project.latitude and project.longitude:
    #     weather = get_daily_report_weather(
    #         project.latitude,
    #         project.longitude
    #     )

    # Existing report: USE SAVED WEATHER
    weather = None

    if report and any([
        report.weather_condition,
        report.weather_temperature,
        report.weather_max_temperature,
        report.weather_min_temperature,
        report.weather_rain_probability,
        report.weather_rainfall,
        report.weather_wind_speed,
        report.weather_humidity,
    ]):
        weather = {
            "condition": report.weather_condition or "",
            "temperature": report.weather_temperature or "",
            "max_temperature": report.weather_max_temperature or "",
            "min_temperature": report.weather_min_temperature or "",
            "rain_probability": report.weather_rain_probability or "",
            "rainfall": report.weather_rainfall or "",
            "wind_speed": report.weather_wind_speed or "",
            "humidity": report.weather_humidity or "",
        }

    elif project.latitude and project.longitude:
        weather = get_daily_report_weather(
            project.latitude,
            project.longitude
        )

    context = {
        "project": project,
        "team_members": team_members,
        "today": today,
        "tomorrow": tomorrow,
        "report_data": report_data,
        "tasks": tasks,
        "all_tasks": all_tasks,
        "future_tasks": future_tasks,
        "all_future_tasks": all_future_tasks,
        "issues": issues,
        "all_issues": all_issues,
        "deliveries": deliveries,
        "all_deliveries": all_deliveries,
        "incidents": incidents,
        "files": files,
        "weather": weather,
        "contractors": contractors,
        "page": "report/create_report.html",
    }

    if request.htmx:
        return render(request, "report/create_report.html", context)
    return render(request, "client/base.html", context)


# ============= Create Issue =============
def test_form_view(request):
    return render(
        request,
        "partials/test_form.html",
    )


# ============= Create Issue =============
def create_report_issue(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    # Assigned Team Member
    assigned_to_id = request.POST.get("team_id")
    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    # SAVE REPORT TASK
    issue = IssueModel.objects.create(
        project=project,
        title=request.POST.get("title"),
        description=request.POST.get("description"),
        priority=request.POST.get("priority"),
        type='issue',
        assigned_to=assigned_to,
        due_date=request.POST.get("due_date"),
        created_by=current_user,
    )

    # =============== Save Photos Evidence ===============
    files = request.FILES.getlist("files")
    for i in files:
        ProjectUploadedFiles.objects.create(
            issue=issue,
            caption=issue.title,
            photo=i,
            project=project,
            uploaded_by_user=current_user,
        )

    # message = f"Issue {issue.title} added successfully."
    message = "Issue added successfully."

    # GET CREATED TASKS
    all_issues = IssueModel.objects.filter(
        Q(project=project) & Q(type='issue') &
        (
            Q(status='open') |
            Q(created_at__date=today)
        )).order_by('-created_at')

    issues = all_issues[:4]

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Issue Created',
        description=f'{current_user.first_name} {current_user.last_name} created an issue - {issue.title}',
        icon_type='issue',
    )

    if assigned_to:
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Issue Assigned',
            description=f'{current_user.first_name} {current_user.last_name} assigned - {issue.title} - issue to {assigned_to.first_name} {assigned_to.last_name}',
            icon_type='issue',
        )

    return render(
        request,
        "partials/issues_report_partial.html",
        {
            "team_members": team_members,
            "project": project,
            "message": message,
            "issues": issues,
            "all_issues": all_issues,
        },
    )


# ============= Create Task =============
def create_report_task(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    # Assigned Team Member
    assigned_to_id = request.POST.get("team_id")
    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    # SAVE REPORT TASK
    issue = IssueModel.objects.create(
        project=project,
        title=request.POST.get("title"),
        description=request.POST.get("description"),
        priority=request.POST.get("priority"),
        type='task',
        assigned_to=assigned_to,
        due_date=request.POST.get("due_date"),
        created_by=current_user,
    )

    # =============== Save Photos Evidence ===============
    files = request.FILES.getlist("files")
    for i in files:
        ProjectUploadedFiles.objects.create(
            issue=issue,
            caption=issue.title,
            photo=i,
            project=project,
            uploaded_by_user=current_user,
        )

    # message = f"Task {issue.title} added successfully."
    message = "Task added successfully."

    # GET CREATED TASKS
    all_tasks = IssueModel.objects.filter(
        Q(project=project) &
        Q(type='task') &
        Q(status='open') &
        (
            Q(due_date__lte=today) |
            Q(created_at__date=today, due_date__isnull=True)
        )
    ).order_by('-created_at')

    tasks = all_tasks[:4]

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Task Created',
        description=f'{current_user.first_name} {current_user.last_name} created a task - {issue.title}',
        icon_type='tasks',
    )

    if assigned_to:
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Task Assigned',
            description=f'{current_user.first_name} {current_user.last_name} assigned - {issue.title} - task to {assigned_to.first_name} {assigned_to.last_name}',
            icon_type='tasks',
        )

    return render(
        request,
        "partials/tasks_report_partial.html",
        {
            "team_members": team_members,
            "project": project,
            "message": message,
            "tasks": tasks,
            "all_tasks": all_tasks,
        },
    )


# ============= Create Planned Work =============
def create_report_planned_work(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()
    tomorrow = timezone.now().date() + timedelta(days=1)

    # Assigned Team Member
    assigned_to_id = request.POST.get("team_id")
    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    # SAVE REPORT TASK
    issue = IssueModel.objects.create(
        project=project,
        title=request.POST.get("title"),
        description=request.POST.get("description"),
        priority=request.POST.get("priority"),
        type='task',
        assigned_to=assigned_to,
        due_date=request.POST.get("due_date"),
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("work_attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                issue_task=issue,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                issue_task=issue,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    message = "Work added successfully."

    # GET CREATED TASKS
    all_future_tasks = IssueModel.objects.filter(
        Q(project=project) &
        Q(type='task') &
        Q(status='open') &
        Q(due_date__gt=today)
    ).order_by('due_date', '-created_at')

    future_tasks = all_future_tasks[:4]

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Task Created',
        description=f'{current_user.first_name} {current_user.last_name} created a task - {issue.title}',
        icon_type='tasks',
    )

    if assigned_to:
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Task Assigned',
            description=f'{current_user.first_name} {current_user.last_name} assigned - {issue.title} - task to {assigned_to.first_name} {assigned_to.last_name}',
            icon_type='tasks',
        )

    return render(
        request,
        "partials/planned_work.html",
        {
            "team_members": team_members,
            "project": project,
            "message": message,
            "future_tasks": future_tasks,
            "all_future_tasks": all_future_tasks,
            "tomorrow": tomorrow,
        },
    )


# ============= Add Report Delivery =============
def add_report_delivery(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

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
    attachments = request.FILES.getlist("delivery_attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                delivery=delivery,
                caption=delivery.reference,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                delivery=delivery,
                caption=delivery.reference,
                file=attachment,
                uploaded_by_user=current_user,
            )

    all_deliveries = DeliveryModel.objects.filter(
        Q(project=project) & Q(delivery_date=today)).order_by('-created_at')[:4]

    deliveries = all_deliveries[:4]

    # =============== CREATE PROJECT TIMELINE ===============
    ActivityModel.objects.create(
        company=company,
        project=project,
        user=current_user,
        activity_type='Delivery Created',
        description=f'{current_user.first_name} {current_user.last_name} added a delivery - {delivery.reference}',
        icon_type='delivery',
    )

    # message = f"Delivery {delivery.reference} added successfully."
    message = "Delivery added successfully."

    return render(
        request,
        "partials/delivery_report_partial.html",
        {
            "project": project,
            "deliveries": deliveries,
            "all_deliveries": all_deliveries,
            "message": message,
            "today": today,
        },
    )


# ============= Add Incident =============
def log_incident(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now()

    # Assigned Team Member
    assigned_to_id = request.POST.get("team_id")
    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

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

    # =============== ATTACHMENTS ===============
    attachments = request.FILES.getlist("attachments")
    for attachment in attachments:
        ProjectUploadedFiles.objects.create(
            project=project,
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

    all_incidents = IncidentModel.objects.filter(
        Q(project=project) & Q(incident_date=today)).order_by('-created_at')
    incidents = all_incidents[:4]

    message = "Incident added successfully."

    return render(
        request,
        "partials/incident_report_partial.html",
        {
            "incidents": incidents,
            "all_incidents": all_incidents,
            "project": project,
            "message": message,
            "today": today,
        },
    )


# ============= DELETE=============
def upload_file_partial(request, report_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    report = get_object_or_404(DailyReportModel, uuid=report_uuid)
    project = report.project

    caption = f"{report.report_date} - 'Daily Report'"

    # =============== ATTACHMENTS ===============
    files = request.FILES.getlist("files")
    for i in files:
        ProjectImages.objects.create(
            reference=report.uuid,
            report=report,
            caption=caption,
            photo=i,
            project=project,
            uploaded_by_user=current_user,
        )

    files = ProjectImages.objects.filter(
        Q(report=report) & Q(reference=report.uuid))

    return render(
        request,
        "partials/attachments_report_partial.html",
        {
            "files": files,
        },
    )


# ============= SAVE FULL REPORT =============
@require_POST
def save_full_report(request, report_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    report = get_object_or_404(DailyReportModel, uuid=report_uuid)
    project = report.project
    today = timezone.now()

    if request.method == 'POST' and 'submit_report' in request.POST:
        status = 'submitted'
        completed_by = current_user
        completed_at = today
        messages.success(
            request,
            f"✅ Daily report submitted successfully."
        )

    if request.method == 'POST' and 'save_draft' in request.POST:
        status = 'draft'
        completed_by = None
        completed_at = None
        messages.success(
            request,
            f"✅ Daily report saved as draft."
        )

    # Report Details
    work_start_time = request.POST.get("work_start_time")
    if work_start_time:
        work_start = work_start_time
    else:
        work_start = None

    work_end_time = request.POST.get("work_end_time")
    if work_end_time:
        work_end = work_end_time
    else:
        work_end = None

    report.foreman = request.POST.get("foreman")
    report.superintendent = request.POST.get("superintendent")
    report.work_start_time = work_start
    report.work_end_time = work_end

    # Weather Conditions Fix *****
    report.weather_condition = request.POST.get("weather_condition") or ""
    report.weather_temperature = request.POST.get(
        "weather_temperature") or None
    report.weather_min_temperature = request.POST.get(
        "weather_min_temperature"
    ) or None
    report.weather_max_temperature = request.POST.get(
        "weather_max_temperature"
    ) or None
    report.weather_rain_probability = request.POST.get(
        "weather_rain_probability"
    ) or None
    report.weather_rainfall = request.POST.get(
        "weather_rainfall"
    ) or None
    report.weather_wind_speed = request.POST.get(
        "weather_wind_speed"
    ) or None
    report.weather_humidity = request.POST.get(
        "weather_humidity"
    ) or None
    report.weather_comment = request.POST.get("weather_comment") or ""

    # Site Attendance
    report.workers_count = request.POST.get("workers_count")
    report.contractors_count = request.POST.get("contractors_count")
    report.visitors_count = request.POST.get("visitors_count")
    report.workers_comment = request.POST.get("workers_comment")
    report.contractors_comment = request.POST.get("contractors_comment")
    report.visitors_comment = request.POST.get("visitors_comment")

    # Toolbox Talk
    report.toolbox_talk_held = request.POST.get("toolbox_held")
    report.toolbox_attendees_count = request.POST.get("total_attendees")
    report.toolbox_talk_topic = request.POST.get("toolbox_topic")
    report.safety_issues = request.POST.get("toolbox_notes")

    # Work Completed
    report.work_completed = request.POST.get("work_completed")

    # Delays
    report.delays = request.POST.get("delays")

    # Additional Notes
    report.notes = request.POST.get("notes")

    report.completed_by = completed_by
    report.status = status
    report.completed_at = completed_at
    report.save()

    # =============== FILES ===============
    attachments = request.FILES.getlist("report_attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                report=report,
                caption=report.reference,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                report=report,
                caption=report.reference,
                file=attachment,
                uploaded_by_user=current_user,
            )

    if status == 'submitted':
        # =============== CREATE PROJECT TIMELINE ===============
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Daily Report Submitted',
            description=f'{current_user.first_name} {current_user.last_name} submitted a daily report',
            icon_type='report',
        )
    elif status == 'draft':
        # =============== CREATE PROJECT TIMELINE ===============
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Daily Report Draft',
            description=f'{current_user.first_name} {current_user.last_name} saved daily report as draft',
            icon_type='report',
        )

    # 🎯 Redirect To Projects
    url = reverse('projects:project-view', args=[project.uuid, ])
    return redirect(f"{url}#DailyReport")


# ============= Missed Daily Report =============
def MissedDailyReports(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    missed_reports_days = get_missed_report_days(project=project)

    context = {
        "missed_reports_days": missed_reports_days,
        "page": "report/missed_reports.html",
    }

    if request.htmx:
        return render(request, "report/missed_reports.html", context)
    return render(request, "client/base.html", context)


# ============= PROJECT REPORTS =============
def ProjectReportsPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    reports = DailyReportModel.objects.filter(
        project=project).order_by('-created_at')
    context = {
        "reports": reports,
        "page": "report/project_reports.html",
    }

    if request.htmx:
        return render(request, "report/project_reports.html", context)
    return render(request, "client/base.html", context)

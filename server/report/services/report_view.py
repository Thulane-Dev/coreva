from django.apps import apps
from django.db.models import Q
from datetime import date
from django.utils import timezone
from collections import defaultdict
from datetime import timedelta


from inspections.services.inspections_view import (
    get_project_details_inspection_data
)


# Models Import
IssueModel = apps.get_model(
    "issues", "IssueModel")

DailyReportModel = apps.get_model(
    "report", "DailyReportModel")

DeliveryModel = apps.get_model(
    "projects", "DeliveryModel")

IncidentModel = apps.get_model(
    "incidents", "IncidentModel")

ProjectUploadedFiles = apps.get_model(
    "projects", "ProjectUploadedFiles")

ActivityModel = apps.get_model(
    "projects", "ActivityModel")


# Models Import
InspectionCategoryModel = apps.get_model(
    "inspections", "InspectionCategoryModel")
InspectionModel = apps.get_model(
    "inspections", "InspectionModel")
InspectionQuestionModel = apps.get_model(
    "inspections", "InspectionQuestionModel")
InspectionResponseModel = apps.get_model(
    "inspections", "InspectionResponseModel")


def generate_daily_report_reference(report_date):
    return f"DR-{report_date.strftime('%Y%m%d')}"


def get_daily_report(
        project,
        current_user=None,
):
    today = timezone.now()

    current_report = DailyReportModel.objects.filter(
        Q(project=project) & Q(report_date=today)).first()

    # =========================
    # GET REPORT OR CREATE ONE
    # =========================
    if current_report == None:
        report_date = timezone.now().date()
        reference = generate_daily_report_reference(report_date)

        current_report = DailyReportModel.objects.create(
            reference=reference,
            project=project,
            report_date=today,
            status='draft',
            created_by=current_user,
        )
        # =============== CREATE PROJECT TIMELINE ===============
        company = current_user.company
        ActivityModel.objects.create(
            company=company,
            project=project,
            user=current_user,
            activity_type='Daily Report Created',
            description=f'{current_user.first_name} {current_user.last_name} created a daily report',
            icon_type='report',
        )
    else:
        current_report = current_report

    # REPORT DATE
    report_date = current_report.report_date

    # =========================
    # TASKS
    # =========================
    # tasks = IssueModel.objects.filter(
    #     Q(project=project) &
    #     Q(type='task') &
    #     (
    #         Q(status='open') |
    #         Q(created_at__date=today)
    #     )
    # ).order_by('-created_at')

    # TASKS: Due today, overdue, or created today with no future due date
    tasks = IssueModel.objects.filter(
        Q(project=project) &
        Q(type='task') &
        Q(status='open') &
        (
            Q(due_date__lte=today) |
            Q(created_at__date=today, due_date__isnull=True)
        )
    ).order_by('-created_at')

    # FUTURE TASKS: Due after today
    future_tasks = IssueModel.objects.filter(
        Q(project=project) &
        Q(type='task') &
        Q(status='open') &
        Q(due_date__gt=today)
    ).order_by('due_date', '-created_at')


    # =========================
    # ISSUES
    # =========================
    issues = IssueModel.objects.filter(
        Q(project=project) & Q(type='issue') &
        (
            Q(status='open') |
            Q(created_at__date=today)
        )).order_by('-created_at')

    # =========================
    # DELIVERIES
    # =========================
    deliveries = DeliveryModel.objects.filter(
        Q(project=project) & Q(delivery_date=today)).order_by('-created_at')

    # =========================
    # INCIDENTS
    # =========================
    incidents = IncidentModel.objects.filter(
        Q(project=project) & Q(incident_date=today)).order_by('-created_at')

    # =========================
    # FILES
    # =========================
    files = ProjectUploadedFiles.objects.filter(
        Q(report=current_report))

    # =========================
    # New Daily Inspections
    # =========================
    inspection = InspectionModel.objects.filter(
        Q(created_at__date=today) & Q(project=project)
    ).first()

    if inspection:
        daily_inspection_data = get_project_details_inspection_data(
            inspection=inspection)
        categories = daily_inspection_data['grouped_checklist']
        inspection_status = daily_inspection_data['inspection_status']
        inspection_btn = daily_inspection_data['inspection_btn']
    else:
        categories = {}
        inspection_status = 'Not Started'
        inspection_btn = 'Start Inspection'

    return {
        "report": current_report,
        "tasks": tasks,
        "future_tasks": future_tasks,
        "issues": issues,
        "deliveries": deliveries,
        "incidents": incidents,
        "files": files,

        # DAILY INSPECTION
        "categories": categories,
        "inspection_status": inspection_status,
        "inspection_btn": inspection_btn,
    }


def get_missed_report_days(project):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    current_date = project.start_date
    missed_days = []

    while current_date <= yesterday:

        # Only count Monday-Friday
        if current_date.weekday() < 5:

            report_exists = DailyReportModel.objects.filter(
                project=project,
                report_date=current_date,
                status="complete",
            ).exists()

            if not report_exists:
                missed_days.append(current_date)

        current_date += timedelta(days=1)

    return missed_days

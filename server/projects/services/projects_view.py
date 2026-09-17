from django.apps import apps
from datetime import date
from django.db.models import Q
from itertools import groupby
from django.utils import timezone
from datetime import timedelta


# Services Import
from inspections.services.inspections_view import (
    get_project_daily_inspection,
    get_project_details_daily_inspection
)

from issues.services.issues_view import (
    get_project_issues,
    get_project_tasks
)

# Models import
DailyReportModel = apps.get_model(
    "report", "DailyReportModel")
ActivityModel = apps.get_model(
    "projects", "ActivityModel")
IncidentModel = apps.get_model(
    "incidents", "IncidentModel")
DeliveryModel = apps.get_model(
    "projects", "DeliveryModel")


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


def get_project_data(
        project,
        current_user=None,
):
    today = timezone.now()
    project_status_count = 0

    # ==================================================
    # Inspections Functions
    # ==================================================
    inspections_data = get_project_details_daily_inspection(
        project=project, current_user=current_user)
    unanswered_count = inspections_data['unanswered_count']
    project_status_count += unanswered_count

    # ==================================================
    # Issues Functions
    # ==================================================
    issues_data = get_project_issues(project=project)
    open_issues_count = issues_data['open_issues_count']
    project_status_count += open_issues_count

    # ==================================================
    # Tasks Functions
    # ==================================================
    tasks_data = get_project_tasks(project=project)
    tasks_count = tasks_data['open_task_count']
    project_status_count += tasks_count

    # ==================================================
    # DAILY REPORT
    # ==================================================
    report = DailyReportModel.objects.filter(
        Q(project=project) & Q(report_date=today)).first()

    if report == None:
        report = None
        report_status = 'Pending'
        report_icon = '🔴'
        report_insight = 'Daily report not started'
        report_action = 'Start Report'
        project_status_count += 1
    elif report.status == 'submitted':
        report = report
        report_status = 'Complete'
        report_icon = '🟢'
        report_insight = 'Daily report complete ✅'
        report_action = 'View Report'
    else:
        report = report
        report_status = 'Incomplete'
        report_icon = '🟡'
        report_insight = 'Daily report incomplete'
        report_action = 'Continue Report'
        project_status_count += 1

    missed_report_days = get_missed_report_days(project)
    missed_report_count = len(missed_report_days)
    if missed_report_count > 0:
        missed_report_icon = '🔴'
        if missed_report_count > 1:
            missed_report_text = f'{missed_report_count} daily reports were missed'
        else:
            missed_report_text = f'{missed_report_count} daily report missed'
    else:
        missed_report_icon = ''
        missed_report_text = ''

    # ==================================================
    # Incidents
    # ==================================================
    incidents = IncidentModel.objects.filter(
        Q(project=project) & Q(incident_date=today)).order_by('-created_at')

    # ==================================================
    # Deliveries
    # ==================================================
    deliveries = DeliveryModel.objects.filter(
        Q(project=project) & Q(delivery_date=today)).order_by('-created_at')

    # ==================================================
    # Activity
    # ==================================================
    activities = ActivityModel.objects.filter(
        Q(project=project) & Q(created_at__date=today)).order_by('-created_at')

    total_activities = activities.count()
    activities = activities[:5]

    grouped_activities = []

    for date, activities_on_date in groupby(
        activities,
        key=lambda activity: timezone.localtime(activity.created_at).date()
    ):
        grouped_activities.append({
            "date": date,
            "activities": list(activities_on_date),
        })

    if project_status_count > 0:
        overall_status = 'Needs Attention'
    else:
        overall_status = 'Everything in order'

    return {
        # "inspection_status": daily_inspection['inspection_status'],
        # "inspection_btn": daily_inspection['inspection_btn'],
        # "inspection_insight": daily_inspection['inspection_insight'],
        # "inspections_questions_count": daily_inspection['inspections_questions_count'],
        # "todays_inspection": daily_inspection['todays_inspection'],
        # "grouped_checklist": daily_inspection['grouped_checklist'],

        # OVERALL STATUS
        "overall_status": overall_status,

        "missed_inspections_text": inspections_data['missed_inspections_text'],
        "missed_inspection_count": inspections_data['missed_inspection_count'],
        "missed_inspection_icon": inspections_data['missed_inspection_icon'],
        "missed_inspection_days": inspections_data['missed_inspection_days'],
        "inspection_status": inspections_data['inspection_status'],
        "inspection_btn": inspections_data['inspection_btn'],
        "inspection_icon": inspections_data['inspection_icon'],
        "inspection_insight": inspections_data['inspection_insight'],
        "failed_inspections": inspections_data['failed_inspections'],
        "inspection_action": inspections_data['inspection_action'],
        "inspections_questions_count": inspections_data['questions_count'],
        "unanswered_count": inspections_data['unanswered_count'],
        "inspection_answered": inspections_data['answered_count'],
        "inspections_questions_count_new": inspections_data['total_checklists'],
        "inspection_percentage": inspections_data['inspection_percentage'],




        "todays_inspection": None,
        "checklist_items": inspections_data['checklist_items'],

        # ISSUES DATA
        "show_issue_insight": issues_data["show_issue_insight"],
        "open_issues": issues_data["open_issues"][:4],
        "issues_insight_text": issues_data['issues_insight_text'],
        "issues_icon": issues_data['issues_icon'],
        "overdue_text": issues_data['overdue_text'],
        "overdue_text_sm": issues_data['overdue_text_sm'],
        "open_issues_count": issues_data['open_issues_count'],
        "open_issues_count": open_issues_count,

        # TASKS DATA
        "open_tasks": tasks_data["open_tasks_sorted"][:4],
        "show_task_insight": tasks_data['show_task_insight'],
        "tasks_insight_text": tasks_data['tasks_insight_text'],
        "tasks_icon": tasks_data['tasks_icon'],
        "overdue_task_text": tasks_data['overdue_task_text'],
        "overdue_task_text_sm": tasks_data['overdue_task_text_sm'],

        "overdue_tasks_count": tasks_data['overdue_tasks_count'],
        "high_priority_tasks": tasks_data['high_priority_count'],
        "tasks_count": tasks_count,

        # DAILY REPORT
        "report": report,
        "report_status": report_status,
        "report_insight": report_insight,
        "report_icon": report_icon,
        "report_action": report_action,
        "missed_report_count": missed_report_count,
        "missed_report_icon": missed_report_icon,
        "missed_report_text": missed_report_text,
        "missed_report_days": missed_report_days,

        # Activities
        "grouped_activities": grouped_activities,
        "total_activities": total_activities,

        # Incidents
        "incidents": incidents,

        # Deliveries
        "deliveries": deliveries,

    }

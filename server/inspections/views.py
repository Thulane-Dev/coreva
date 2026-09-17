from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone


# Models Import
from .models import *
from authentication.models import UserModel
from issues.models import *
from projects.models import *

# Services Import
from .services.inspections_view import (
    get_inspection_data,
    get_project_daily_inspection_new,
    get_missed_inspection_days
)


# ============= Daily Inspection View =============
def DailyInspectionView(request, inspection_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    inspection = get_object_or_404(InspectionModel, uuid=inspection_uuid)
    inspection_data = get_inspection_data(
        inspection=inspection, current_user=current_user)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')

    context = {
        "inspection": inspection,
        "inspection_data": inspection_data,
        "team_members": team_members,
        "page": "inspections/inspection.html",
    }

    if request.htmx:
        return render(request, "inspections/inspection.html", context)
    return render(request, "client/base.html", context)


# ============= Daily Inspection View =============
def DailyInspectionPartialView(request, inspection_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    inspection = get_object_or_404(InspectionModel, uuid=inspection_uuid)
    inspection_data = get_inspection_data(
        inspection=inspection, current_user=current_user)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')

    context = {
        "inspection": inspection,
        "inspection_data": inspection_data,
        "team_members": team_members,
        "page": "partials/inspections_partial.html",
    }

    if request.htmx:
        return render(request, "partials/inspections_partial.html", context)
    return render(request, "client/base.html", context)


# ============= Update Daily Inspection =============
def AnswerInspectionQuestionPost(request, inspection_uuid, question_uuid):
    answer = request.POST.get("answer")

    response = InspectionResponseModel.objects.filter(
        Q(inspection__uuid=inspection_uuid) & Q(question__uuid=question_uuid)).first()
    response.answer = answer
    response.save()

    return DailyInspectionPartialView(request, inspection_uuid)


# ============= Create Issue Post =============
def CreateInspectionIssue(request, inspection_uuid, response_uuid):
    inspection = get_object_or_404(InspectionModel, uuid=inspection_uuid)
    response = InspectionResponseModel.objects.filter(
        Q(inspection__uuid=inspection_uuid) & Q(uuid=response_uuid)).first()

    # Assigned Team Member
    assigned_to_id = request.POST.get("assigned_to")
    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    issue, created = IssueModel.objects.update_or_create(
        # Lookup fields - used to find existing record
        inspection=inspection,
        inspection_response=response,

        # Default fields - used when creating or updating
        defaults={
            'type': 'issue',
            'title': response.question.question,
            'description': request.POST.get("issue_description"),
            'priority': request.POST.get("priority"),
            'due_date': request.POST.get("due_date"),
            'due_time': request.POST.get("due_time"),
            'assigned_to': assigned_to,
        }
    )

    return DailyInspectionPartialView(request, inspection_uuid)


def NewInspectionsView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    inspection_data_new = get_project_daily_inspection_new(
        project=project, current_user=current_user)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    context = {
        "inspection": inspection_data_new['inspection'],
        "inspection_data_new": inspection_data_new,
        "team_members": team_members,
        "today": today,
        "page": "inspections/new_inspections_page.html",
    }

    if request.htmx:
        return render(request, "inspections/new_inspections_page.html", context)
    return render(request, "client/base.html", context)


def update_inspection_response(request, response_id):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    response = get_object_or_404(
        InspectionResponseModel.objects.select_related(
            "question",
            "question__category",
            "inspection",
        ).prefetch_related(
            "inspection_response",
        ),
        id=response_id,
    )

    answer = request.POST.get("answer")

    response.answer = answer
    response.save()

    category = response.question.category
    inspection = response.inspection

    # Get all responses for this category
    category_responses = InspectionResponseModel.objects.filter(
        question__category=category,
        inspection=inspection,
    ).prefetch_related(
        "inspection_response",
    )

    total_questions = category_responses.count()

    total_answered = category_responses.filter(
        answer__isnull=False
    ).exclude(
        answer=""
    ).count()

    failed_items = category_responses.filter(answer="fail").count()

    # =============== CREATE PROJECT TIMELINE  ===============
    if answer == 'fail':
        ActivityModel.objects.create(
            company=company,
            project=response.inspection.project,
            user=current_user,
            activity_type='Inspection Failed',
            description=f'{current_user.first_name} {current_user.last_name} flagged inspection item - {response.question.question} - failed',
            icon_type='inspection',
        )

    return render(
        request,
        "partials/inspection_response_update.html",
        {
            "response": response,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "team_members": team_members,
            "today": today,
            "failed_items": failed_items,
        },
    )


# ============= Create Inspection Issue =============
def create_new_issue(request, response_id):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')

    response = get_object_or_404(
        InspectionResponseModel.objects.select_related(
            "question",
            "question__category",
            "inspection",
        ).prefetch_related(
            "inspection_response",
        ),
        id=response_id,
    )

    # Add Issue ==============
    assigned_to_id = request.POST.get("assigned_to_id")
    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    issue, created = IssueModel.objects.update_or_create(
        # Lookup fields - used to find existing record
        inspection=response.inspection,
        inspection_response=response,

        # Default fields - used when creating or updating
        defaults={
            'type': 'issue',
            'title': response.question.question,
            'description': request.POST.get("description"),
            'priority': request.POST.get("priority"),
            'due_date': request.POST.get("due_date"),
            'assigned_to': assigned_to,
        }
    )

    response = get_object_or_404(
        InspectionResponseModel.objects.select_related(
            "question",
            "question__category",
            "inspection",
        ).prefetch_related(
            "inspection_response",
        ),
        id=response_id,
    )

    category = response.question.category
    inspection = response.inspection

    # Get all responses for this category
    category_responses = InspectionResponseModel.objects.filter(
        question__category=category,
        inspection=inspection,
    ).prefetch_related(
        "inspection_response",
    )

    total_questions = category_responses.count()

    total_answered = category_responses.filter(
        answer__isnull=False
    ).exclude(
        answer=""
    ).count()

    failed_items = category_responses.filter(answer="fail").count()

    # =============== CREATE PROJECT TIMELINE  ===============
    ActivityModel.objects.create(
        company=company,
        project=issue.inspection.project,
        user=current_user,
        activity_type='Issue Created',
        description=f'{current_user.first_name} {current_user.last_name} created an inspection issue - {issue.title}',
        icon_type='issue',
    )

    if assigned_to:
        ActivityModel.objects.create(
            company=company,
            project=issue.inspection.project,
            user=current_user,
            activity_type='Issue Assigned',
            description=f'{current_user.first_name} {current_user.last_name} assigned inspection issue - {issue.title} - to {assigned_to.first_name} {assigned_to.last_name}',
            icon_type='issue',
        )

    return render(
        request,
        "partials/inspection_response_update.html",
        {
            "response": response,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "team_members": team_members,
            "failed_items": failed_items,
        },
    )


# ============= Save Inspection =============
@require_POST
def save_inspection(request, inspection_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    inspection = get_object_or_404(InspectionModel, uuid=inspection_uuid)
    project = inspection.project

    if request.method == 'POST' and 'save_draft' in request.POST:
        status = 'draft'

    if request.method == 'POST' and 'save_inspection' in request.POST:
        status = 'completed'

    # Update Inspection
    inspection.completed_at = timezone.now()
    inspection.completed_by = current_user
    inspection.status = status
    inspection.save()

    messages.success(
        request,
        f"✅ Inspection successfully updated."
    )

    # 🎯 Redirect To Projects
    url = reverse('projects:project-view', args=[project.uuid, ])
    return redirect(f"{url}#inspectionsID")

# ===========================================================================================


# ============= PROJECT DAILY INSPECTIONS =============
def ProjectDailyInspectionsView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    inspection_data_new = get_project_daily_inspection_new(
        project=project, current_user=current_user)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    context = {
        "inspection": inspection_data_new['inspection'],
        "inspection_data_new": inspection_data_new,
        "team_members": team_members,
        "today": today,
        "page": "inspections/project_daily_inspections.html",
    }

    if request.htmx:
        return render(request, "inspections/project_daily_inspections.html", context)
    return render(request, "client/base.html", context)


# ============= Missed Daily Inspections =============
def MissedDailyInspections(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    missed_inspection_days = get_missed_inspection_days(project=project)

    context = {
        "missed_inspection_days": missed_inspection_days,
        "page": "inspections/missed_inspections.html",
    }

    if request.htmx:
        return render(request, "inspections/missed_inspections.html", context)
    return render(request, "client/base.html", context)


def ProjectInspectionsPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    inspections = InspectionModel.objects.filter(
        project=project).order_by('-created_at')

    context = {
        "inspections": inspections,
        "project": project,
        "page": "inspections/project_inspections.html",
    }

    if request.htmx:
        return render(request, "inspections/project_inspections.html", context)
    return render(request, "client/base.html", context)

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

# Models Import
from .models import *
from projects.models import *
from authentication.models import *


from .services.issues_view import (
    get_project_issues,
    get_project_tasks,
    get_all_project_issues,
)


# ============= Issues Page View =============
def IssuesPageView(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project_uuid = 'ccb1971b-57b1-4586-897e-d4880678f59f'
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()

    issues_data = get_project_issues(project=project)
    issues = issues_data['open_issues']

    context = {
        "today": today,
        "issues": issues,
        "current_user": current_user,
        "page": "issues/issues.html",
    }

    if request.htmx:
        return render(request, "issues/issues.html", context)
    return render(request, "client/base.html", context)


# ============= Add Issue =============
def AddIssueView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')
    today = timezone.now()

    current_url = request.resolver_match.url_name
    if current_url == 'add-task':
        page_title = 'Add a Task'
        save_btn = 'Save Task'
        section_text = 'Task'
        description_text = 'Task Description'
        icon = 'bi bi-check2-square'
        sub_title = 'Add a task that needs be completed.'
    else:
        page_title = 'Log a Project Issue'
        save_btn = 'Save Issue'
        section_text = 'Issue'
        description_text = 'Description'
        icon = 'bi bi-exclamation-triangle-fill'
        sub_title = 'Record an issue that needs attention, tracking or resolution.'

    context = {
        "project": project,
        "team_members": team_members,
        "today": today,
        "page_title": page_title,
        "save_btn": save_btn,
        "sub_title": sub_title,
        "section_text": section_text,
        "description_text": description_text,
        "icon": icon,
        "page": "issues/add_issue.html",
    }

    if request.htmx:
        return render(request, "issues/add_issue.html", context)
    return render(request, "client/base.html", context)


# ============= Save New Project Issue =============
@require_POST
def save_issue_post(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    current_url = request.resolver_match.url_name
    # Get just the date
    today = timezone.now().date()

    if request.method == "POST":
        # Assigned Team Member
        assigned_to_id = request.POST.get("team_id")

        if assigned_to_id != 'None':
            assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
        else:
            assigned_to = None

        title = request.POST.get("title")

        save_type = request.POST.get("save_type")
        if save_type == 'Issue':
            return_url = 'issue'
            activity_type = 'Issue Created'
            description_text = 'issue'
            document_type = 'issue'
            caption = title
            messages.success(
                request,
                f"✅ Issue successfully logged."
            )
        else:
            return_url = 'task'
            activity_type = 'Task Created'
            description_text = 'task'
            document_type = 'task'
            caption = title
            messages.success(
                request,
                f"✅ New Task successfully created."
            )

        # =============== Save New Issue ===============
        issue = IssueModel.objects.create(
            project=project,
            type=document_type,
            title=caption,
            description=request.POST.get("description"),
            priority=request.POST.get("priority"),
            assigned_to=assigned_to,
            due_date=request.POST.get("due_date"),
            created_by=current_user,
        )

        # =============== Save Photos Evidence ===============
        files = request.FILES.getlist("files")
        for i in files:
            ProjectImages.objects.create(
                issue=issue,
                caption=caption,
                photo=i,
                project=project,
                uploaded_by_user=current_user,
            )

        # =============== CREATE PROJECT TIMELINE ===============
        # ISSUE TIMELINE
        if save_type == 'Issue':
            ActivityModel.objects.create(
                company=company,
                project=project,
                user=current_user,
                activity_type='Issue Created',
                description=f'{current_user.first_name} {current_user.last_name} created an issue - {caption}',
                icon_type='issue',
            )

            if assigned_to:
                ActivityModel.objects.create(
                    company=company,
                    project=project,
                    user=current_user,
                    activity_type='Issue Assigned',
                    description=f'{current_user.first_name} {current_user.last_name} assigned - {caption} - issue to {assigned_to.first_name} {assigned_to.last_name}',
                    icon_type='issue',
                )
        # TASK TIMELINE
        else:
            ActivityModel.objects.create(
                company=company,
                project=project,
                user=current_user,
                activity_type='Task Created',
                description=f'{current_user.first_name} {current_user.last_name} created a task - {caption}',
                icon_type='tasks',
            )

            if assigned_to:
                ActivityModel.objects.create(
                    company=company,
                    project=project,
                    user=current_user,
                    activity_type='Task Assigned',
                    description=f'{current_user.first_name} {current_user.last_name} assigned - {caption} - task to {assigned_to.first_name} {assigned_to.last_name}',
                    icon_type='tasks',
                )

        url = reverse(
            "projects:project-view",
            kwargs={"project_uuid": project.uuid}
        )

        response = HttpResponse(status=200)

        response["HX-Location"] = json.dumps({
            "path": f"{url}#{return_url}{issue.id}",
            "target": "#content",
            "swap": "innerHTML",
        })

        return response


# ============= Project Issues =============
def ProjectIssuesPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()

    issues_data = get_all_project_issues(project=project)
    issues = issues_data['open_issues']

    context = {
        "today": today,
        "issues": issues,
        "current_user": current_user,
        "project": project,
        "page": "issues/project_issues.html",
    }

    if request.htmx:
        return render(request, "issues/project_issues.html", context)
    return render(request, "client/base.html", context)


# ============= Project Tasks =============
def ProjectTasksPageView(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)
    today = timezone.now().date()

    tasks_data = get_project_tasks(project=project)
    tasks = tasks_data['open_tasks_sorted']

    context = {
        "today": today,
        "tasks": tasks,
        "current_user": current_user,
        "project": project,
        "page": "issues/project_tasks.html",
    }

    if request.htmx:
        return render(request, "issues/project_tasks.html", context)
    return render(request, "client/base.html", context)


# ============= VIEW ISSUE PAGE =============
def IssuePreview(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    # Get the issue and its related objects
    issue = get_object_or_404(
        IssueModel.objects.select_related(
            "project",
            "inspection",
            "inspection_response",
            "daily_report",
            "assigned_to",
            "created_by",
        ),
        uuid=issue_uuid,
    )

    # Comments for this issue
    # comments = (
    #     IssueCommentModel.objects
    #     .filter(issue=issue)
    #     .select_related("comment_by")
    #     .order_by("created_at")
    # )

    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("created_at")
    )

    # Team members available for assignment
    # team_members = (
    #     UserModel.objects
    #     .filter(
    #         company=request.user.company,
    #         status="active",
    #     )
    #     .order_by("first_name", "last_name")
    # )

    team_members = UserModel.objects.filter(
        company=company).order_by('date_created')

    context = {
        "issue": issue,
        "comments": comments,
        "team_members": team_members,
        "today": timezone.localdate(),
        "page": "issues/issue_preview.html",
    }

    if request.htmx:
        return render(request, "issues/issue_preview.html", context)
    return render(request, "client/base.html", context)


# ============= UPDATE ISSUE POST METHOD =============
def save_issue_update(request):

    if request.method == "POST":
        name = request.POST.get("name")

        url = reverse(
            "issues:issues",
        )

        response = HttpResponse(status=200)

        # response["HX-Location"] = json.dumps({
        #     "path": url,
        #     "target": "#content",
        #     "swap": "innerHTML",
        # })

        response["HX-Location"] = json.dumps({
            "path": f"{url}#issueTargetPlaceID",
            "target": "#content",
            "swap": "innerHTML",
        })

        return response


# ============= Save Issue Comment =============
def save_issue_comment(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    project = issue.project

    comment = IssueCommentModel.objects.create(
        issue=issue,
        comment=request.POST.get("comment"),
        comment_by=current_user,
    )

    # =============== FILES ===============
    attachments = request.FILES.getlist("comment_attachments")
    for attachment in attachments:
        if attachment.content_type.startswith("image/"):
            ProjectUploadedFiles.objects.create(
                project=project,
                comment=comment,
                caption=issue.title,
                photo=attachment,
                uploaded_by_user=current_user,
            )
        else:
            ProjectUploadedFiles.objects.create(
                project=project,
                comment=comment,
                caption=issue.title,
                file=attachment,
                uploaded_by_user=current_user,
            )

    # Comments for this issue
    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .prefetch_related("comment_attachments")
        .order_by("created_at")
    )

    message = "Comment added successfully."

    return render(
        request,
        "partials/issue_comments_partial.html",
        {
            "issue": issue,
            "comments": comments,
            "message": message,
        },
    )


# ============= Mark Comment as read =============
def mark_issue_read(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    issue = IssueModel.objects.filter(uuid=issue_uuid).first()

    comment_uuid = request.POST.get("comment_uuid")
    comment = IssueCommentModel.objects.filter(uuid=comment_uuid).first()
    comment.is_read = True
    comment.save()

    # Comments for this issue
    comments = (
        IssueCommentModel.objects
        .filter(issue=issue)
        .select_related("comment_by")
        .order_by("created_at")
    )

    message = "Comment updated successfully."

    return render(
        request,
        "partials/issue_comments_partial.html",
        {
            "issue": issue,
            "comments": comments,
            "message": message,
        },
    )


# ============= Update Issue Status =============
@require_POST
def update_issue_status(request, issue_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    today = timezone.now().date()
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company

    # Assigned Team Member
    assigned_to_id = request.POST.get("assigned_to_id")

    if assigned_to_id != 'None':
        assigned_to = UserModel.objects.filter(id=assigned_to_id).first()
    else:
        assigned_to = None

    issue = IssueModel.objects.filter(uuid=issue_uuid).first()
    issue.status = request.POST.get("status")
    issue.priority = request.POST.get("priority")
    issue.due_date = request.POST.get("due_date")
    issue.assigned_to = assigned_to
    issue.closed_at = today
    issue.assigned_to = assigned_to
    issue.closed_by = current_user
    issue.save()

    messages.success(
        request,
        f"Successfully updated."
    )

    ActivityModel.objects.create(
        company=company,
        project=issue.project,
        user=current_user,
        activity_type=f'Issue {issue.status}',
        description=f'{current_user.first_name} {current_user.last_name} {issue.status} issue - {issue.title}',
        icon_type='issue',
    )

    # 🎯 Redirect To Projects
    url = reverse('issues:issue', args=[issue.uuid, ])
    return redirect(f"{url}")

from django.apps import apps
from django.db.models import Q
from datetime import date
from django.utils import timezone
from collections import defaultdict
from django.db.models import Prefetch


# Models Import
IssueModel = apps.get_model(
    "issues", "IssueModel")
IssueCommentModel = apps.get_model(
    "issues", "IssueCommentModel")


def get_project_issues(
        project
):
    # Open Issues
    open_issues_list = []
    comments_issues_list = []
    high_priority_count = 0
    medium_priority_count = 0
    low_priority_count = 0
    overdue_issues_count = 0

    STATUS_PRIORITY = {
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    open_issues = IssueModel.objects.filter(
        Q(project=project) & Q(status='open') & Q(type='issue')).prefetch_related(
        Prefetch(
            "issue",
            queryset=IssueCommentModel.objects.filter(
                is_read=False).order_by("-created_at"),
            to_attr="unread_comments"
        )
    ).order_by("-created_at")

    for issue in open_issues:
        comment_count = 0
        if issue.priority == 'high':
            icon = '🔴'
            span_css = 'red_background'
            high_priority_count += 1

        elif issue.priority == 'medium':
            icon = '🟡'
            span_css = 'medium_background'
            medium_priority_count += 1

        else:
            icon = '🔵'
            span_css = 'medium_background'
            low_priority_count += 1

        # DAYS LEFT CHECK
        days_left = (
            issue.due_date - date.today()).days

        if days_left < 0:
            issue_text = f"Due {abs(days_left)} days ago"
            overdue_issues_count += 1
            due_css = 'text-danger'

        elif days_left == 0:
            issue_text = "Due today"
            due_css = 'text-danger'

        elif days_left == 1:
            issue_text = "Due tomorrow"
            due_css = 'text-warning'

        else:
            issue_text = f"Due in {days_left} days"
            due_css = 'text-primary'

        # comment check
        for comment in issue.unread_comments:
            comment_count += 1

        if comment_count > 0:
            comments_issues_list.append(issue)

        open_issues_list.append({
            "issue": issue,
            "status": issue.priority,
            "status_icon": icon,
            "span_css": span_css,
            "issue_text": issue_text,
            "due_css": due_css,
            "comment_count": comment_count,
        })

    open_issues_sorted = sorted(
        open_issues_list,
        key=lambda x: STATUS_PRIORITY.get(x["status"], 99)
    )

    open_issues_count = len(open_issues_sorted)
    issues_insight_text = f"{open_issues_count} Issues Open"
    show_issue_insight = False
    issues_icon = ''

    overdue_text = ''
    overdue_text_sm = ''
    if open_issues_count != 0:
        issue_plural = "s" if overdue_issues_count > 1 else ""

        if overdue_issues_count == 1:
            needs_plural = 'needs'
        else:
            needs_plural = 'need'

        show_issue_insight = True
        issues_icon = '🔴'
        issues_insight_text = f"{open_issues_count} issue{issue_plural} {needs_plural} attention"
        overdue_text = f"({overdue_issues_count} overdue issue{issue_plural})"
        overdue_text_sm = f'{overdue_issues_count} overdue issue{issue_plural}'

    return {
        # "open_issues": open_issues_sorted,
        "open_issues": open_issues_list,
        "show_issue_insight": show_issue_insight,
        "issues_insight": issues_insight_text,
        "high_priority_issues": high_priority_count,
        "issues_icon": issues_icon,
        "issues_insight_text": issues_insight_text,
        "overdue_text": overdue_text,
        "overdue_text_sm": overdue_text_sm,
        "open_issues_count": open_issues_count,
        "comments_issues_list": comments_issues_list,
    }


# GET ALL PROJECT ISSUES
def get_all_project_issues(
        project
):
    # Open Issues
    open_issues_list = []
    high_priority_count = 0
    medium_priority_count = 0
    low_priority_count = 0
    overdue_issues_count = 0

    STATUS_PRIORITY = {
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    # open_issues = IssueModel.objects.filter(
    #     Q(project=project) & Q(type='issue')).order_by('-created_at')

    open_issues = IssueModel.objects.filter(
        project=project,
        type="issue"
    ).prefetch_related(
        Prefetch(
            "issue",
            queryset=IssueCommentModel.objects.filter(
                is_read=False).order_by("-created_at"),
            to_attr="unread_comments"
        )
    ).order_by("-created_at")

    for issue in open_issues:
        comment_count = 0
        if issue.priority == 'high':
            icon = '🔴'
            span_css = 'red_background'
            high_priority_count += 1

        elif issue.priority == 'medium':
            icon = '🟡'
            span_css = 'medium_background'
            medium_priority_count += 1

        else:
            icon = '🔵'
            span_css = 'medium_background'
            low_priority_count += 1

        # DAYS LEFT CHECK
        days_left = (
            issue.due_date - date.today()).days

        if days_left < 0:
            issue_text = f"Due {abs(days_left)} days ago"
            overdue_issues_count += 1
            due_css = 'text-danger'

        elif days_left == 0:
            issue_text = "Due today"
            due_css = 'text-danger'

        elif days_left == 1:
            issue_text = "Due tomorrow"
            due_css = 'text-warning'

        else:
            issue_text = f"Due in {days_left} days"
            due_css = 'text-primary'

        # comment check
        for comment in issue.unread_comments:
            comment_count += 1

        open_issues_list.append({
            "issue": issue,
            "status": issue.priority,
            "status_icon": icon,
            "span_css": span_css,
            "issue_text": issue_text,
            "due_css": due_css,
            "comment_count": comment_count,
        })

    open_issues_sorted = sorted(
        open_issues_list,
        key=lambda x: STATUS_PRIORITY.get(x["status"], 99)
    )

    open_issues_count = len(open_issues_sorted)
    issues_insight_text = f"{open_issues_count} Issues Open"
    show_issue_insight = False
    issues_icon = ''

    overdue_text = ''
    overdue_text_sm = ''
    if open_issues_count != 0:
        issue_plural = "s" if overdue_issues_count > 1 else ""

        if overdue_issues_count == 1:
            needs_plural = 'needs'
        else:
            needs_plural = 'need'

        show_issue_insight = True
        issues_icon = '🔴'
        issues_insight_text = f"{open_issues_count} issue{issue_plural} {needs_plural} attention"
        overdue_text = f"({overdue_issues_count} overdue issue{issue_plural})"
        overdue_text_sm = f'{overdue_issues_count} overdue issue{issue_plural}'

    return {
        # "open_issues": open_issues_sorted,
        "open_issues": open_issues_list,
        "show_issue_insight": show_issue_insight,
        "issues_insight": issues_insight_text,
        "high_priority_issues": high_priority_count,
        "issues_icon": issues_icon,
        "issues_insight_text": issues_insight_text,
        "overdue_text": overdue_text,
        "overdue_text_sm": overdue_text_sm,
        "open_issues_count": open_issues_count,
        "open_issues_count": open_issues_count,
    }


def filter_issues(
    project
):
    # Open Issues
    open_issues_list = []

    open_issues = IssueModel.objects.filter(
        project=project,
        type="issue"
    ).prefetch_related(
        Prefetch(
            "issue",
            queryset=IssueCommentModel.objects.filter(
                is_read=False).order_by("-created_at"),
            to_attr="unread_comments"
        )
    ).order_by("-created_at")

    for issue in open_issues:
        comment_count = 0

        # DAYS LEFT CHECK
        days_left = (
            issue.due_date - date.today()).days

        if days_left < 0:
            issue_text = f"Due {abs(days_left)} days ago"

        elif days_left == 0:
            issue_text = "Due today"

        elif days_left == 1:
            issue_text = "Due tomorrow"

        else:
            issue_text = f"Due in {days_left} days"

        # comment check
        for comment in issue.unread_comments:
            comment_count += 1

        open_issues_list.append({
            "issue": issue,
            "issue_text": issue_text,
            "comment_count": comment_count,
        })

    return {
        # "open_issues": open_issues_sorted,
        "open_issues": open_issues_list,
    }


def get_project_tasks(
        project,
):
    # Open Issues
    open_task_list = []
    comments_tasks_list = []
    high_priority_count = 0
    medium_priority_count = 0
    low_priority_count = 0
    overdue_tasks_count = 0

    STATUS_PRIORITY = {
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    open_tasks = IssueModel.objects.filter(
        Q(project=project) & Q(status='open') & Q(type='task')).prefetch_related(
        Prefetch(
            "issue",
            queryset=IssueCommentModel.objects.filter(
                is_read=False).order_by("-created_at"),
            to_attr="unread_comments"
        )
    ).order_by("-created_at")

    for task in open_tasks:
        comment_count = 0
        if task.priority == 'high':
            span_css = 'bg-danger'
            high_priority_count += 1
            text_dark_priority = ''
            border_color = 'red_border_right'

        elif task.priority == 'medium':
            span_css = 'bg-warning'
            medium_priority_count += 1
            text_dark_priority = 'text-dark'
            border_color = 'orange_border_right'

        else:
            span_css = 'bg-primary'
            low_priority_count += 1
            text_dark_priority = ''
            border_color = 'green_border_right'

        # check days left
        days_left = (
            task.due_date - date.today()).days

        if days_left < 0:
            task_text = f"Due {abs(days_left)} days ago"
            due_css = 'text-danger'
            text_dark = ''
            overdue_tasks_count += 1

        elif days_left == 0:
            task_text = "Due today"
            due_css = 'text-danger'
            text_dark = ''

        elif days_left == 1:
            task_text = "Due tomorrow"
            due_css = 'text-warning'
            text_dark = 'text-dark'

        else:
            task_text = f"Due in {days_left} days"
            due_css = 'text-primary'
            text_dark = ''

        # comment check
        for comment in task.unread_comments:
            comment_count += 1

        if comment_count > 0:
            comments_tasks_list.append(task)

        open_task_list.append({
            "task": task,
            "status": task.priority,
            "span_css": span_css,
            "task_text": task_text,
            "due_css": due_css,
            "text_dark": text_dark,
            "text_dark_priority": text_dark_priority,
            "border_color": border_color,
            "comment_count": comment_count,
        })

    open_tasks_sorted = sorted(
        open_task_list,
        key=lambda x: STATUS_PRIORITY.get(x["status"], 99)
    )

    open_task_count = len(open_tasks_sorted)
    tasks_insight_text = f"{open_task_count} Tasks Incomplete"
    show_task_insight = False
    tasks_icon = ''
    overdue_task_text = ''
    overdue_task_text_sm = ''
    if open_task_count != 0:
        task_plural = "s" if open_task_count > 1 else ""
        if open_task_count == 1:
            needs_plural = 'needs'
        else:
            needs_plural = 'need'

        show_task_insight = True
        tasks_icon = '🔴'
        tasks_insight_text = f"{open_task_count} task{task_plural} {needs_plural} to be completed"
        overdue_task_text = f'( {overdue_tasks_count} overdue task{task_plural} )'
        overdue_task_text_sm = f'{overdue_tasks_count} overdue task{task_plural}'

    return {
        # "open_tasks_sorted": open_tasks_sorted,
        "open_tasks_sorted": open_task_list,
        "show_task_insight": show_task_insight,
        "tasks_insight_text": tasks_insight_text,
        "tasks_icon": tasks_icon,
        "overdue_task_text": overdue_task_text,
        "high_priority_count": high_priority_count,
        "open_task_count": open_task_count,
        "overdue_tasks_count": overdue_tasks_count,
        "overdue_task_text_sm": overdue_task_text_sm,
        "comments_tasks_list": comments_tasks_list,
    }


def get_all_project_tasks(
        project,
):
    # Open Issues
    open_task_list = []
    high_priority_count = 0
    medium_priority_count = 0
    low_priority_count = 0
    overdue_tasks_count = 0

    STATUS_PRIORITY = {
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    # open_tasks = IssueModel.objects.filter(
    #     Q(project=project) & Q(status='open') & Q(type='task')).order_by('-created_at')

    open_tasks = IssueModel.objects.filter(
        project=project,
        type="task"
    ).prefetch_related(
        Prefetch(
            "issue",
            queryset=IssueCommentModel.objects.filter(
                is_read=False).order_by("-created_at"),
            to_attr="unread_comments"
        )
    ).order_by("-created_at")

    for task in open_tasks:
        comment_count = 0
        if task.priority == 'high':
            span_css = 'bg-danger'
            high_priority_count += 1
            text_dark_priority = ''
            border_color = 'red_border_right'

        elif task.priority == 'medium':
            span_css = 'bg-warning'
            medium_priority_count += 1
            text_dark_priority = 'text-dark'
            border_color = 'orange_border_right'

        else:
            span_css = 'bg-primary'
            low_priority_count += 1
            text_dark_priority = ''
            border_color = 'green_border_right'

        # check days left
        days_left = (
            task.due_date - date.today()).days

        if days_left < 0:
            task_text = f"Due {abs(days_left)} days ago"
            due_css = 'text-danger'
            text_dark = ''
            overdue_tasks_count += 1

        elif days_left == 0:
            task_text = "Due today"
            due_css = 'text-danger'
            text_dark = ''

        elif days_left == 1:
            task_text = "Due tomorrow"
            due_css = 'text-warning'
            text_dark = 'text-dark'

        else:
            task_text = f"Due in {days_left} days"
            due_css = 'text-primary'
            text_dark = ''

        # comment check
        for comment in task.unread_comments:
            comment_count += 1

        open_task_list.append({
            "task": task,
            "status": task.priority,
            "span_css": span_css,
            "task_text": task_text,
            "due_css": due_css,
            "text_dark": text_dark,
            "text_dark_priority": text_dark_priority,
            "border_color": border_color,
            "comment_count": comment_count,
        })

    open_tasks_sorted = sorted(
        open_task_list,
        key=lambda x: STATUS_PRIORITY.get(x["status"], 99)
    )

    open_task_count = len(open_tasks_sorted)
    tasks_insight_text = f"{open_task_count} Tasks Incomplete"
    show_task_insight = False
    tasks_icon = ''
    overdue_task_text = ''
    overdue_task_text_sm = ''
    if open_task_count != 0:
        task_plural = "s" if open_task_count > 1 else ""
        if open_task_count == 1:
            needs_plural = 'needs'
        else:
            needs_plural = 'need'

        show_task_insight = True
        tasks_icon = '🔴'
        tasks_insight_text = f"{open_task_count} task{task_plural} still {needs_plural} to be completed"
        overdue_task_text = f'( {overdue_tasks_count} overdue task{task_plural} )'
        overdue_task_text_sm = f'{overdue_tasks_count} overdue task{task_plural}'

    return {
        # "open_tasks_sorted": open_tasks_sorted,
        "open_tasks_sorted": open_task_list,
        "show_task_insight": show_task_insight,
        "tasks_insight_text": tasks_insight_text,
        "tasks_icon": tasks_icon,
        "overdue_task_text": overdue_task_text,
        "high_priority_count": high_priority_count,
        "open_task_count": open_task_count,
        "overdue_tasks_count": overdue_tasks_count,
        "overdue_task_text_sm": overdue_task_text_sm,
    }

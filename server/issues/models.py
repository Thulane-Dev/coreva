from django.db import models
from django.utils import timezone

# Models Import
from authentication.models import *
from account.models import *
from inspections.models import *
from report.models import *

# Create your models here.


class IssueModel(models.Model):
    TYPE_CHOICES = (
        ("issue", "Issue"),
        ("task", "Task"),
    )

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )

    STATUS_CHOICES = (
        ("open", "Open"),
        ("closed", "Closed"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(ProjectModel, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='project_issue')
    inspection = models.ForeignKey(InspectionModel, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='inspection_issue')
    inspection_response = models.ForeignKey(InspectionResponseModel, null=True, blank=True,
                                            on_delete=models.SET_NULL, related_name='inspection_response')
    daily_report = models.ForeignKey(DailyReportModel, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='daily_report')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="issue")
    priority = models.CharField(
        max_length=50, choices=PRIORITY_CHOICES, default="low")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open")
    assigned_to = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, null=True, blank=True, related_name="assigned_to")
    closed_by = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, null=True, blank=True, related_name="closed_by")
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, null=True, blank=True, related_name="created_by")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def due_status(self):
        if not self.due_date:
            return None

        today = timezone.localdate()
        days = (today - self.due_date).days

        if days > 0:
            if days == 1:
                return "Due 1 day ago"
            return f"Due {days} days ago"

        if days == 0:
            return "Due today"

        days_until_due = abs(days)

        if days_until_due == 1:
            return "Due tomorrow"

        return f"Due in {days_until_due} days"

    def __str__(self):
        return f"{self.title} - {self.priority}"


class IssueCommentModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    issue = models.ForeignKey(IssueModel, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='issue')
    comment = models.TextField(blank=True)
    comment_by = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, null=True, blank=True, related_name="comment_by")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.issue.title} - {self.comment}"

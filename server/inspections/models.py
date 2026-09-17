from django.db import models
import uuid

# Models import
from projects.models import ProjectModel
from authentication.models import UserModel


class InspectionCategoryModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(blank=True)
    is_default = models.BooleanField(default=True)
    project = models.ForeignKey(ProjectModel, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='project_category')
    not_applicable = models.ManyToManyField(
        ProjectModel, blank=True, default=None, related_name='na_category')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.order}"


class InspectionQuestionModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.ForeignKey(InspectionCategoryModel, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='category')
    question = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(blank=True)
    is_default = models.BooleanField(default=True)
    project_question = models.ForeignKey(ProjectModel, null=True, blank=True,
                                         on_delete=models.SET_NULL, related_name='project_question')
    not_applicable = models.ManyToManyField(
        ProjectModel, blank=True, default=None, related_name='na_question')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.question} - {self.order}"


class InspectionModel(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("incomplete", "incomplete"),
        ("completed", "Completed"),
        ("ready", "Ready"),
        ("overdue", "Overdue"),
        ("in_progress", "In Progress"),
        ("draft", "Draft"),
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(ProjectModel, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='project_inspection')
    inspection_date = models.DateField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="started_by")
    completed_by = models.ForeignKey(
        'authentication.UserModel', null=True, blank=True, on_delete=models.SET_NULL, related_name="completed_by")
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.started_at} - {self.completed_at}"


class InspectionResponseModel(models.Model):
    ANSWER_CHOICES = (
        ("pass", "Pass"),
        ("fail", "Fail"),
        ("na", "N/A"),
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    inspection = models.ForeignKey(InspectionModel, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='inspection_model')
    question = models.ForeignKey(InspectionQuestionModel, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='inspection_question')
    answer = models.CharField(
        max_length=10, choices=ANSWER_CHOICES, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inspection.project.project_name} - {self.question.question} - {self.answer}"

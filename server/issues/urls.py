
from django.urls import path
from .import views

app_name = "issues"

urlpatterns = [
    path('issues/',
         views.IssuesPageView, name='issues'),
    path('log-issue/<uuid:project_uuid>/',
         views.AddIssueView, name='log-issue'),
    path('add-task/<uuid:project_uuid>/',
         views.AddIssueView, name='add-task'),
    path('save-issue/<uuid:project_uuid>/',
         views.save_issue_post, name='save-issue'),
    path('project-issues/<uuid:project_uuid>/',
         views.ProjectIssuesPageView, name='project-issues'),
    path('project-tasks/<uuid:project_uuid>/',
         views.ProjectTasksPageView, name='project-tasks'),
    # UPDATE ISSUE URLS
    path('issue/<uuid:issue_uuid>/',
         views.IssuePreview, name='issue'),
    path('update-issue-status/<uuid:issue_uuid>/',
         views.update_issue_status, name='update-issue-status'),
    path('update-issue/',
         views.save_issue_update, name='update-issue'),
    path('save-issue-comment/<uuid:issue_uuid>/',
         views.save_issue_comment, name='save-issue-comment'),
    path('mark-issue-read/<uuid:issue_uuid>/',
         views.mark_issue_read, name='mark-issue-read'),
]

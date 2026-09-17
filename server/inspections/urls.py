
from django.urls import path
from .import views

app_name = "inspections"

urlpatterns = [
    path('inspection/<uuid:inspection_uuid>/',
         views.DailyInspectionView, name='inspection'),

    path('inspection-new/<uuid:project_uuid>/',
         views.NewInspectionsView, name='inspection-new'),
    path('answer-inspection-question/<uuid:inspection_uuid>/<uuid:question_uuid>/',
         views.AnswerInspectionQuestionPost, name='answer-inspection-question'),
    path('create-inspection-issue/<uuid:inspection_uuid>/<uuid:response_uuid>/',
         views.CreateInspectionIssue, name='create-inspection-issue'),
    path('update-inspection-response/<int:response_id>/',
         views.update_inspection_response, name='update-inspection-response'),
    path('add-issue/<int:response_id>/',
         views.create_new_issue, name='add-issue'),
    path('save-inspection/<uuid:inspection_uuid>/',
         views.save_inspection, name='save-inspection'),

    # NEW URLS
    path('checklist/<uuid:project_uuid>/',
         views.ProjectDailyInspectionsView, name='checklist'),
    path('missed-inspections/<uuid:project_uuid>/',
         views.MissedDailyInspections, name='missed-inspections'),

    path('project-inspections/<uuid:project_uuid>/',
         views.ProjectInspectionsPageView, name='project-inspections'),
]

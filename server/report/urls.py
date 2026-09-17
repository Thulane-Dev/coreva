
from django.urls import path
from .import views

app_name = "report"

urlpatterns = [
    path('report/',
         views.ReportView, name='report'),
    path('create-report/<uuid:project_uuid>/',
         views.CreateReportView, name='create-report'),


    # Latest urls
    path('issue-save-daily/<uuid:project_uuid>/',
         views.create_report_issue, name='issue-save-daily'),
    path('save-report-task/<uuid:project_uuid>/',
         views.create_report_task, name='save-report-task'),
    path('save-report-incident/<uuid:project_uuid>/',
         views.log_incident, name='save-report-incident'),
    path('save-delivery-item/<uuid:project_uuid>/',
         views.add_report_delivery, name='save-delivery-item'),
    path('save-report-planned-work/<uuid:project_uuid>/',
         views.create_report_planned_work, name='save-report-planned-work'),


    path('save-report/<uuid:report_uuid>/',
         views.save_full_report, name='save-report'),


    path('missed-daily-reports/<uuid:project_uuid>/',
         views.MissedDailyReports, name='missed-daily-reports'),
    path('project-reports/<uuid:project_uuid>/',
         views.ProjectReportsPageView, name='project-reports'),


    path('files-upload/<uuid:report_uuid>/',
         views.upload_file_partial, name='files-upload'),



    path('test-form-submit/',
         views.test_form_view, name='test-form-submit'),
]

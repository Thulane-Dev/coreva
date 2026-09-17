
from django.urls import path
from .import views

app_name = "projects"

urlpatterns = [
    path('projects/', views.ProjectsView, name='projects'),
    path('add-project/', views.AddProjectView, name='add-project'),
    path('save-new-project', views.save_new_project, name='save-new-project'),
    path('project/<uuid:project_uuid>/',
         views.ProjectDetailsView, name='project'),
    path('project-preview/<uuid:project_uuid>/',
         views.NewProjectDetailsView, name='project-preview'),
    path('add-project-incident/<uuid:project_uuid>/',
         views.add_project_incident, name='add-project-incident'),
    path('add-project-delivery/<uuid:project_uuid>/',
         views.add_project_delivery, name='add-project-delivery'),
    # NEW PROJECT DETAILS PAGE
    path('project-view/<uuid:project_uuid>/',
         views.ProjectDetailsPreviewDetails, name='project-view'),
    path('log-delivery/<uuid:project_uuid>/',
         views.LogProjectDeliveryView, name='log-delivery'),
    path('save-new-delivery/<uuid:project_uuid>/',
         views.save_new_delivery, name='save-new-delivery'),
    path('project-deliveries/<uuid:project_uuid>/',
         views.ProjectDeliveriesPageView, name='project-deliveries'),
    path('project-activity/<uuid:project_uuid>/',
         views.ProjectActivityDetailsPageView, name='project-activity'),
]


from django.urls import path
from .import views

app_name = "incidents"

urlpatterns = [
    path('incidents/',
         views.IncidentsView, name='incidents'),
    path('log-incident/<uuid:project_uuid>/',
         views.LogIncidentView, name='log-incident'),
    path('save-new-incident/<uuid:project_uuid>/',
         views.save_new_incident, name='save-new-incident'),
    path('project-incidents/<uuid:project_uuid>/',
         views.ProjectIncidentsPageView, name='project-incidents'),
]

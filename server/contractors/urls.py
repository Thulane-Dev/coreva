
from django.urls import path
from .import views

app_name = "contractors"

urlpatterns = [
    path('contractors/',
         views.ContractorsView, name='contractors'),
    path('add-contractor/<uuid:project_uuid>/',
         views.AddContractorView, name='add-contractor'),
    path('save-contractor/<uuid:project_uuid>/',
         views.save_contractor, name='save-contractor'),
]

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages

# Models Import
from .models import *
from account.models import *
from authentication.models import *
from projects.models import *


# ============= Contractors =============
def ContractorsView(request):

    context = {
        "page": "contractors/contractors.html",
    }

    if request.htmx:
        return render(request, "contractors/contractors.html", context)
    return render(request, "client/base.html", context)


# ============= Add Contractor View =============
def AddContractorView(request, project_uuid):
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    context = {
        "project": project,
        "page": "contractors/add_contractor.html",
    }

    if request.htmx:
        return render(request, "contractors/add_contractor.html", context)
    return render(request, "client/base.html", context)


# ============= Save Account Setup =============
@require_POST
def save_contractor(request, project_uuid):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)
    company = current_user.company
    project = get_object_or_404(ProjectModel, uuid=project_uuid)

    # Create Address Model Object
    save_address = AddressModel.objects.create(
        street_address=request.POST.get("street"),
        city=request.POST.get("city"),
        province=request.POST.get("province"),
        country=request.POST.get("country"),
    )

    # Create Company Profile Model Object
    save_contractor = CompanyProfileModel.objects.create(
        company_name=request.POST.get("company_name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        address=save_address,
    )

    # Create relationship
    SubcontractorRelation.objects.create(
        main_contractor=company,
        subcontractor=save_contractor,
        created_by=current_user,
    )

    # Add To Project
    ProjectContractor.objects.create(
        project=project,
        contractor=save_contractor,
        added_by=current_user,
    )

    messages.success(
        request,
        f"✅ {save_contractor.company_name} successfully added."
    )

    # 🎯 Redirect To Projects
    url = reverse('projects:project', args=[project.uuid, ])
    return redirect(f"{url}#Contractors")

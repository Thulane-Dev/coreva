from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages

# Models Import
from .models import *
from authentication.models import *


# ============= Account Setup View =============
def AccountSetupView(request):
    work_days = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
        ("sunday", "Sunday"),
    ]

    context = {
        "work_days": work_days,
    }
    return render(request, 'account/account_setup.html', context)


# ============= Save Account Setup =============
@require_POST
def save_account_setup(request):
    user = request.user
    current_user = get_object_or_404(UserModel, user=user)

    # Create Address Model Object
    save_address = AddressModel.objects.create(
        street_address=request.POST.get("street"),
        city=request.POST.get("city"),
        province=request.POST.get("province"),
        country=request.POST.get("country"),
    )

    # Check if company logo uploaded
    logo = request.FILES.get("logo")
    if logo:
        uploaded_logo = logo
    else:
        uploaded_logo = None

    # Create Company Profile Model Object
    save_company = CompanyProfileModel.objects.create(
        company_name=request.POST.get("company_name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        address=save_address,
        logo=uploaded_logo
    )

    # Update User Account Details
    current_user.company = save_company
    current_user.account_complete = True
    current_user.save()

    messages.success(
        request,
        f"🎉 Account successfully setup."
    )

    # 🎯 Redirect To Dashboard
    url = reverse('dashboard:todays-work')
    return redirect(f"{url}")


# ============= Account View =============
def AccountView(request):

    context = {
        "page": "account/account.html",
    }

    if request.htmx:
        return render(request, "account/account.html", context)
    return render(request, "client/base.html", context)

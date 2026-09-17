from django.db import models
import uuid

# Create your models here.


class AddressModel(models.Model):
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    province = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.street_address} - {self.city} {self.province}"


class CompanyProfileModel(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('de-active', 'De-Active'),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    company_name = models.CharField(max_length=255, blank=True)
    address = models.ForeignKey(
        AddressModel, on_delete=models.CASCADE, null=True, blank=True)
    industry = models.CharField(max_length=200, default="Construction")
    phone = models.CharField(max_length=50, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(
        upload_to="company_logo/", null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.industry}"

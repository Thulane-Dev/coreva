from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ProjectModel)
admin.site.register(ProjectUserModel)
admin.site.register(ProjectImages)
admin.site.register(DeliveryModel)
admin.site.register(DeliveredItemsModel)
admin.site.register(ActivityModel)
admin.site.register(ProjectContractor)
# admin.site.register(ProjectFilesUpload)
admin.site.register(ProjectUploadedFiles)

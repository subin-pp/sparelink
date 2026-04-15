from django.contrib import admin
from .models import VehicleBrand, VehicleModel, Part, Listing

admin.site.register(VehicleBrand)
admin.site.register(VehicleModel)
admin.site.register(Part)
admin.site.register(Listing)

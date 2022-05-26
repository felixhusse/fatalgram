from django.contrib import admin

from .models import Person, Photo, Trip

# Register your models here.
admin.site.register(Trip)
admin.site.register(Photo)
admin.site.register(Person)

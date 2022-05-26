from django.contrib import admin

from .models import Person, PersonEncoding, Photo, Trip

# Register your models here.
admin.site.register(Trip)
admin.site.register(Photo)
admin.site.register(Person)
admin.site.register(PersonEncoding)

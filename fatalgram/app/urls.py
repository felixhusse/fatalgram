from django.urls import path

from fatalgram.app.views import home, photo_upload

app_name = "app"

urlpatterns = [
    path("", view=home, name="home"),
    path("upload", view=photo_upload, name="upload"),
]

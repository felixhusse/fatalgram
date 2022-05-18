from django.urls import path

from fatalgram.app.views import home

app_name = "app"

urlpatterns = [
    path("", view=home, name="home"),
]

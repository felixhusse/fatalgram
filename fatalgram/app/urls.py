from django.urls import path

from fatalgram.app.views import (
    clear_persons,
    delete_gallery,
    home,
    person_recognize,
    photo_upload,
    rescan_gallery,
    test_scan,
)

app_name = "app"

urlpatterns = [
    path("", view=home, name="home"),
    path("upload", view=photo_upload, name="upload"),
    path("about", view=person_recognize, name="about"),
    path("admin/gallery/delete", view=delete_gallery, name="delete_gallery"),
    path("admin/facerecognition/test", view=test_scan, name="test_scan"),
    path("admin/facerecognition/rescan", view=rescan_gallery, name="rescan_gallery"),
    path("admin/facerecognition/delete", view=clear_persons, name="clear_persons"),
]

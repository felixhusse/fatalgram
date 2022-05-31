from django.urls import path

from fatalgram.app.views import (
    FileFieldFormView,
    clear_persons,
    delete_gallery,
    gallery_admin,
    home,
    rescan_gallery,
    test_scan,
)

app_name = "app"

urlpatterns = [
    path("", view=home, name="home"),
    path("admin/gallery", view=gallery_admin, name="admin"),
    path("photoupload", view=FileFieldFormView.as_view(), name="photoupload"),
    path("admin/gallery/delete", view=delete_gallery, name="delete_gallery"),
    path("admin/facerecognition/test", view=test_scan, name="test_scan"),
    path("admin/facerecognition/rescan", view=rescan_gallery, name="rescan_gallery"),
    path("admin/facerecognition/delete", view=clear_persons, name="clear_persons"),
]

import datetime

from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404, render

from .models import Trip
from .service import PhotoService


def home(request):
    now = datetime.datetime.now()
    return render(request, "pages/home.html", {"time": now})


def photo_upload(request):
    if request.method == "POST" and request.FILES["photozip"]:
        photozip = request.FILES["photozip"]
        trip_id = request.POST.get("trip_id")
        fs = FileSystemStorage()
        filename = fs.save("fatalgram/temp/" + photozip.name, photozip)
        uploaded_file_url = fs.url(filename)
        trip = get_object_or_404(Trip, pk=trip_id)
        photoService = PhotoService()
        result = photoService.processZipFile(
            trip=trip, photozip=fs.path(filename), user=request.user
        )
        return render(
            request,
            "fatalgram/admin/upload.html",
            {"uploaded_file_url": uploaded_file_url, "result": result},
        )

    return render(request, "fatalgram/admin/upload.html", {})

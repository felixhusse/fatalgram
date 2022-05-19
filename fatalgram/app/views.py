import datetime

from django.core.files.storage import FileSystemStorage
from django.shortcuts import render

from .service import PhotoService


def home(request):
    now = datetime.datetime.now()
    return render(request, "pages/home.html", {"time": now})


def photo_upload(request):
    if request.method == "POST" and request.FILES["photozip"]:
        photozip = request.FILES["photozip"]
        fs = FileSystemStorage()
        filename = fs.save("gallery/temp/" + photozip.name, photozip)
        uploaded_file_url = fs.url(filename)
        photoService = PhotoService()
        result = photoService.processZipFile(
            photozip=fs.path(filename), user=request.user
        )
        return render(
            request,
            "pages/upload.html",
            {"uploaded_file_url": uploaded_file_url, "result": result},
        )

    return render(request, "pages/upload.html", {})

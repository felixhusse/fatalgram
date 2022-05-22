from django.core.files.storage import FileSystemStorage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

from .models import Photo
from .tasks import process_photo_zip


def home(request):
    photo_list = Photo.objects.all().order_by("description").reverse()

    page = request.GET.get("page", 1)
    paginator = Paginator(photo_list, 10)
    try:
        photos = paginator.page(page)
    except PageNotAnInteger:
        photos = paginator.page(1)
    except EmptyPage:
        photos = paginator.page(paginator.num_pages)
    return render(request, "pages/home.html", {"photos": photos})


def photo_upload(request):
    if request.method == "POST" and request.FILES["photozip"]:
        photozip = request.FILES["photozip"]
        fs = FileSystemStorage()
        filename = fs.save("gallery/temp/" + photozip.name, photozip)

        process_photo_zip.delay(filename=filename, user_id=request.user.id)

        uploaded_file_url = fs.url(filename)

        return render(
            request,
            "pages/upload.html",
            {"uploaded_file_url": uploaded_file_url},
        )

    return render(request, "pages/upload.html", {})

from django.core.files.storage import FileSystemStorage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.shortcuts import render

from .models import Person, Photo
from .service import FaceService, PhotoService
from .tasks import process_faces, process_photo_zip


def home(request):

    photo_list = Photo.objects.all().order_by("description").reverse()

    if request.method == "GET" and "person" in request.GET:
        person_id = int(request.GET["person"])
        person = Person.objects.get(pk=person_id)
        photo_list = person.photos.all().order_by("description").reverse()

    persons = Person.objects.all()
    page = request.GET.get("page", 1)
    paginator = Paginator(photo_list, 10)
    try:
        photos = paginator.page(page)
    except PageNotAnInteger:
        photos = paginator.page(1)
    except EmptyPage:
        photos = paginator.page(paginator.num_pages)
    return render(request, "pages/home.html", {"photos": photos, "persons": persons})


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


def person_recognize(request):

    return render(request, "pages/about.html", {})


def clear_persons(request):
    face_service = FaceService()

    for person in Person.objects.all():
        face_service.delete_person(person)

    return JsonResponse({"result": "done"})


def delete_gallery(request):
    photo_list = Photo.objects.all()
    photo_service = PhotoService()
    face_service = FaceService()

    for person in Person.objects.all():
        face_service.delete_person(person)

    for photo in photo_list:
        photo_service.delete_photo(photo_pk=photo.id)

    return JsonResponse({"result": "done"})


def rescan_gallery(request):
    photo_list = Photo.objects.all()
    for photo in photo_list:
        process_faces.delay(photo_id=photo.id, user_id=request.user.id)
    return JsonResponse({"result": "done"})


def test_scan(request):
    return JsonResponse({"result": "no function implemented"})

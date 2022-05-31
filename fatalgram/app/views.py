from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.views.generic.edit import FormView

from .forms import FileFieldForm
from .models import Person, Photo
from .service import FaceService, PhotoService
from .tasks import process_faces, process_photo_image, process_photo_zip


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


def gallery_admin(request):
    if request.method == "POST" and request.FILES["photozip"]:
        photozip = request.FILES["photozip"]
        fs = FileSystemStorage()
        filename = fs.save("gallery/temp/" + photozip.name, photozip)
        process_photo_zip.delay(filename=filename, user_id=request.user.id)
        uploaded_file_url = fs.url(filename)

        return render(
            request,
            "pages/admin.html",
            {"uploaded_file_url": uploaded_file_url},
        )

    return render(
        request,
        "pages/admin.html",
        {},
    )


class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = "pages/photoupload.html"  # Replace with your template.
    success_url = "/photoupload"  # Replace with your URL or reverse().

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Images uploaded.")
        return reverse("app:photoupload")

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist("file_field")
        fs = FileSystemStorage()
        if form.is_valid():
            for file in files:
                filename = fs.save("gallery/temp/" + file.name, file)
                process_photo_image.delay(
                    photo_image=fs.path(filename), user_id=request.user.id
                )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


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

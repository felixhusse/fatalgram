from celery import Celery
from django.core.files.storage import FileSystemStorage

from fatalgram.users.models import User

from .models import Photo
from .service import FaceService, PhotoService

app = Celery("fatalgram")


@app.task(name="process-photo-zip")
def process_photo_zip(filename, user_id):
    fs = FileSystemStorage()
    photo_service = PhotoService()
    user = User.objects.get(pk=user_id)
    photo_service.process_zip_file(photozip=fs.path(filename), user=user)


@app.task(name="process-faces")
def process_faces(photo_id, user_id):
    photo = Photo.objects.get(pk=photo_id)
    user = User.objects.get(pk=user_id)
    face_service = FaceService()
    face_service.recognize_faces(photo=photo, user=user)

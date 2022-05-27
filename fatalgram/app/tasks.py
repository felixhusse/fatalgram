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
    photo_images = photo_service.extract_zip_file(photozip=fs.path(filename))
    for photo_image in photo_images:
        process_photo_image.delay(photo_image=photo_image, user_id=user_id)


@app.task(name="process-photo-image")
def process_photo_image(photo_image, user_id):
    user = User.objects.get(pk=user_id)
    photo_service = PhotoService()
    photo_id = photo_service.process_photo(photo_path=photo_image, user=user)
    process_faces.delay(photo_id=photo_id, user_id=user_id)


@app.task(name="process-faces")
def process_faces(photo_id, user_id):
    photo = Photo.objects.get(pk=photo_id)
    user = User.objects.get(pk=user_id)
    face_service = FaceService()
    face_service.recognize_faces(photo=photo, user=user)

from celery import Celery
from django.core.files.storage import FileSystemStorage

from fatalgram.users.models import User

from .service import PhotoService

app = Celery("fatalgram")


@app.task(name="process-photo-zip")
def process_photo_zip(filename, user_id):
    fs = FileSystemStorage()
    photo_service = PhotoService()
    user = User.objects.get(pk=user_id)
    photo_service.process_zip_file(photozip=fs.path(filename), user=user)

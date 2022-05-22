from celery import Celery
from django.core.files.storage import FileSystemStorage

from fatalgram.users.models import User

from .service import PhotoService

app = Celery("fatalgram")


@app.task(name="process-photo-zip")
def process_photo_zip(filename, user_id):
    fs = FileSystemStorage()
    photoService = PhotoService()
    user = User.objects.get(pk=user_id)
    photoService.processZipFile(photozip=fs.path(filename), user=user)

import os
import tempfile
from datetime import datetime
from zipfile import ZipFile

from django.core.files import File
from GPSPhoto import gpsphoto
from PIL import ExifTags, Image, ImageOps

from .models import Photo, Trip


class PhotoService:
    def deletePhoto(self, photo_pk):
        photo = Photo.objects.get(pk=photo_pk)
        photo.delete()
        return

    def processZipFile(self, photozip, user):
        with tempfile.TemporaryDirectory() as tmpdirname:
            with ZipFile(photozip, "r") as zippedImgs:
                for filename in zippedImgs.namelist():
                    if "MACOSX" not in filename and (
                        ".jpg" in filename or ".JPG" in filename
                    ):
                        zippedImgs.extract(filename, path=tmpdirname)
            self.importFolder(photo_folder=tmpdirname, user=user)
        os.remove(photozip)
        return

    def importFolder(self, photo_folder, user):
        for dirName, subdirList, fileList in os.walk(photo_folder):
            for fname in fileList:
                self.processPhoto(photo_path=os.path.join(dirName, fname), user=user)

    def get_exif(self, url):
        img = Image.open(url)
        exif = {
            ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS
        }
        return exif

    def generateThumbnail(self, photo_path, photo):
        size = (300, 300)
        thumb = ImageOps.fit(Image.open(photo_path), size, Image.ANTIALIAS)
        filename, ext = os.path.splitext(os.path.basename(photo_path))
        thumb.save(os.path.dirname(photo_path) + "/" + filename + "_thumbnail.jpg")
        image_thumb = File(
            open(os.path.dirname(photo_path) + "/" + filename + "_thumbnail.jpg", "rb")
        )
        photo.photo_thumb.save(filename + "_thumbnail.jpg", image_thumb)

    def processPhoto(self, photo_path, user):
        exifData = self.get_exif(photo_path)
        gpsData = gpsphoto.getGPSData(photo_path)
        photo_name = os.path.basename(photo_path)
        image_raw = File(open(photo_path, "rb"))

        photo = Photo(description=photo_name, author=user)
        photo.photo_raw.save(photo_name, image_raw)
        photo.photo_taken = datetime.strptime(exifData["DateTime"], "%Y:%m:%d %H:%M:%S")
        photo.photo_camera = exifData["Model"]
        photo.photo_lat = gpsData["Latitude"]
        photo.photo_lon = gpsData["Longitude"]
        photo.photo_alt = gpsData["Altitude"]
        photo.save()
        self.generateThumbnail(photo_path=photo_path, photo=photo)


class TripService:
    def createTrip(self, title, startDate, endDate, summary, user):
        trip = Trip(
            author=user,
            title=title,
            summary=summary,
            trip_date=startDate,
            trip_end=endDate,
        )
        trip.save()
        return trip

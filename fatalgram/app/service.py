import os
import tempfile
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

import face_recognition
from django.core.files import File
from GPSPhoto import gpsphoto
from PIL import ExifTags, Image, ImageOps

from .models import Person, Photo, Trip


class FaceService:
    def delete_person(self, person):
        person.face_thumb.delete()
        person.delete()

    def create_person(self, face_encoding, face_thumb, user, photo):
        person = Person(
            name="unknown person", face_encoding=str(face_encoding), author=user
        )
        person.save()
        person.photos.add(photo)
        blob = BytesIO()
        face_thumb.save(blob, "jpeg")
        person.face_thumb.save(f"{person.id}_face.jpg", File(blob))
        return person

    def create_face_thumb(self, image_file, face_location):
        face_image = face_recognition.load_image_file(image_file)
        top, right, bottom, left = face_location
        face_image = face_image[top:bottom, left:right]
        pil_image = Image.fromarray(face_image)
        return pil_image

    def create_face_encodings(self, image_file):
        face_image = face_recognition.load_image_file(image_file)
        face_locations = face_recognition.face_locations(face_image)
        face_encodings = face_recognition.face_encodings(face_image)
        return {"face_locations": face_locations, "face_encodings": face_encodings}

    def check_faces(self, face_encoding, photo):
        persons = Person.objects.all()
        for person in persons:
            known_encodings = []
            for person_encoding in person.face_encoding:
                string_array = person_encoding.face_encoding[1:-1].split()
                known_encodings.append(list(map(float, string_array)))

            result = face_recognition.compare_faces(known_encodings, face_encoding)
            if True in result:
                person.photos.add(photo)
                return True
        return False


class PhotoService:
    def deletePhoto(self, photo_pk):
        photo = Photo.objects.get(pk=photo_pk)
        photo.photo_raw.delete()
        photo.photo_thumb.delete()
        photo.delete()

    def processZipFile(self, photozip, user):
        with tempfile.TemporaryDirectory() as tmpdirname:
            with ZipFile(photozip, "r") as zippedImgs:
                for filename in zippedImgs.namelist():
                    if "MACOSX" not in filename and (".jpg" in filename or ".JPG"):
                        zippedImgs.extract(filename, path=tmpdirname)
            self.importFolder(photo_folder=tmpdirname, user=user)
        os.remove(photozip)
        return

    def importFolder(self, photo_folder, user):
        for dirName, subdirList, fileList in os.walk(photo_folder):
            for fname in fileList:
                if ".jpg" in fname or ".JPG" in fname:
                    self.processPhoto(
                        photo_path=os.path.join(dirName, fname), user=user
                    )

    def get_exif(self, url):
        img = Image.open(url)
        try:
            exif = {
                ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in ExifTags.TAGS
            }
        except AttributeError:
            exif = {}
        return exif

    def generateThumbnail(self, photo_path, photo):
        size = (300, 300)
        try:
            image = Image.open(photo_path)
            if hasattr(image, "_getexif"):  # only present in JPEGs
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == "Orientation":
                        break
                e = image._getexif()  # returns None if no EXIF data
                if e is not None:
                    exif = dict(e.items())
                    orientation = exif[orientation]

                    if orientation == 3:
                        image = image.transpose(Image.ROTATE_180)
                    elif orientation == 6:
                        image = image.transpose(Image.ROTATE_270)
                    elif orientation == 8:
                        image = image.transpose(Image.ROTATE_90)

            image = ImageOps.fit(image, size, Image.ANTIALIAS)
            filename, ext = os.path.splitext(os.path.basename(photo_path))

            image.save(os.path.dirname(photo_path) + "/" + filename + "_thumbnail.jpg")
            image_thumb = File(
                open(
                    os.path.dirname(photo_path) + "/" + filename + "_thumbnail.jpg",
                    "rb",
                )
            )
            photo.photo_thumb.save(filename + "_thumbnail.jpg", image_thumb)

        except AttributeError:
            pass

    def processPhoto(self, photo_path, user):
        exifData = self.get_exif(photo_path)
        gpsData = gpsphoto.getGPSData(photo_path)
        photo_name = os.path.basename(photo_path)
        image_raw = File(open(photo_path, "rb"))

        photo = Photo(description=photo_name, author=user)
        photo.photo_raw.save(photo_name, image_raw)
        try:
            photo.photo_taken = datetime.strptime(
                exifData["DateTime"], "%Y:%m:%d %H:%M:%S"
            )
            photo.photo_camera = exifData["Model"]
        except KeyError:
            pass

        try:
            photo.photo_lat = gpsData["Latitude"]
            photo.photo_lon = gpsData["Longitude"]
            photo.photo_alt = gpsData["Altitude"]
        except KeyError:
            pass

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

    def find_faces(self, img):
        # Load the jpg files into numpy arrays
        lydia_image = face_recognition.load_image_file(
            "media/test/lydia/training/lydia.jpg"
        )
        unknown_image = face_recognition.load_image_file(
            "media/test/lydia/test/" + img + ".jpg"
        )

        # Get the face encodings for each face in each image file
        # Since there could be more than one face in each image, it returns a list of encodings.
        # But since I know each image only has one face, I only care about the first encoding
        # in each image, so I grab index 0.
        try:
            lydia_face_encoding = face_recognition.face_encodings(lydia_image)[0]
            # pix = os.listdir("/train_dir/" + person)

            unknown_face_encodings = face_recognition.face_encodings(unknown_image)
        except IndexError:
            print(
                "I wasn't able to locate any faces in at least one of the images. Check the image files. Aborting..."
            )
            quit()

        known_faces = [lydia_face_encoding]

        # results is an array of True/False telling if the unknown face matched anyone in the known_faces array
        print(f"Faces found: {len(unknown_face_encodings)}")
        for unknown_face_encoding in unknown_face_encodings:
            results = face_recognition.compare_faces(known_faces, unknown_face_encoding)
            print(f"Is the unknown face a picture of Lydia? {results[0]}")

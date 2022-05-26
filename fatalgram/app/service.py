import os
import tempfile
from io import BytesIO
from zipfile import ZipFile

import face_recognition
from django.core.files import File
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
    def delete_photo(self, photo_pk):
        photo = Photo.objects.get(pk=photo_pk)
        photo.photo_raw.delete()
        photo.photo_thumb.delete()
        photo.delete()

    def process_zip_file(self, photozip, user):
        with tempfile.TemporaryDirectory() as tmpdirname:
            with ZipFile(photozip, "r") as zippedImgs:
                for filename in zippedImgs.namelist():
                    if "MACOSX" not in filename and (".jpg" in filename or ".JPG"):
                        zippedImgs.extract(filename, path=tmpdirname)
            self.import_folder(photo_folder=tmpdirname, user=user)
        os.remove(photozip)
        return

    def import_folder(self, photo_folder, user):
        for dirName, subdirList, fileList in os.walk(photo_folder):
            for fname in fileList:
                if ".jpg" in fname or ".JPG" in fname:
                    self.process_photo(
                        photo_path=os.path.join(dirName, fname), user=user
                    )

    def process_photo(self, photo_path, user):
        photo_name = os.path.basename(photo_path)
        image_raw = File(open(photo_path, "rb"))
        photo = Photo(description=photo_name, author=user)
        photo.photo_raw.save(photo_name, image_raw)
        photo.save()
        pil_image = self.correct_orientation(pil_image=Image.open(photo_path))
        photo.photo_thumb.save(
            photo_name + "_sm.jpg",
            self.generate_thumb(pil_image=pil_image, size=(300, 300), fit_size=True),
        )
        photo.photo_high.save(
            photo_name + "_hq.jpg",
            self.generate_thumb(pil_image=pil_image, size=(1920, 1920), fit_size=False),
        )
        photo.photo_medium.save(
            photo_name + "_md.jpg",
            self.generate_thumb(pil_image=pil_image, size=(1080, 1080), fit_size=False),
        )

    def correct_orientation(self, pil_image):
        if hasattr(pil_image, "_getexif"):  # only present in JPEGs
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == "Orientation":
                    break
            e = pil_image._getexif()  # returns None if no EXIF data
            if e is not None:
                exif = dict(e.items())
                orientation = exif[orientation]

                if orientation == 3:
                    pil_image = pil_image.transpose(Image.ROTATE_180)
                elif orientation == 6:
                    pil_image = pil_image.transpose(Image.ROTATE_270)
                elif orientation == 8:
                    pil_image = pil_image.transpose(Image.ROTATE_90)
        return pil_image

    def generate_thumb(self, pil_image, size, fit_size):
        modified_image = pil_image.copy()
        if fit_size is True:
            modified_image = ImageOps.fit(modified_image, size, Image.ANTIALIAS)
        else:
            modified_image.thumbnail(size, Image.ANTIALIAS)

        image_blob = BytesIO()
        modified_image.save(image_blob, "jpeg")
        return image_blob


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

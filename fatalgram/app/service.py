import os
from io import BytesIO
from zipfile import ZipFile

import face_recognition
from django.core.files import File
from PIL import ExifTags, Image, ImageOps

from .models import Person, PersonEncoding, Photo


class FaceService:
    def recognize_faces(self, photo, user):
        face_image = face_recognition.load_image_file(photo.photo_high.path)
        face_locations = face_recognition.face_locations(face_image)
        face_encodings = face_recognition.face_encodings(face_image)
        # check if person is already there
        for index, face_encoding in enumerate(face_encodings):
            found_person = self.check_person(face_encoding=face_encoding)
            if found_person is None:
                # create a new person
                found_person = Person(name="Unknown Person", author=user)
                found_person.save()

            found_person.photos.add(photo)
            person_encoding = PersonEncoding(
                face_encoding=face_encoding, person=found_person
            )
            person_encoding.save()
            face_thumb = self.create_face_thumb(
                image_file=photo.photo_high.path, face_location=face_locations[index]
            )
            person_encoding.face_thumb.save(
                f"{found_person.id}_face.jpg", File(face_thumb)
            )
            person_encoding.save()

    def check_person(self, face_encoding):
        persons = Person.objects.all()
        for person in persons:
            known_encodings = []
            for person_encoding in person.personencoding_set.all():
                known_encoding = person_encoding.face_encoding[1:-1].split()
                known_encodings.append(list(map(float, known_encoding)))
            result = face_recognition.compare_faces(known_encodings, face_encoding)
            if True in result:
                return person

        return None

    def delete_person(self, person):
        for personencoding in person.personencoding_set.all():
            personencoding.face_thumb.delete()
        person.delete()

    def create_face_thumb(self, image_file, face_location):
        face_image = face_recognition.load_image_file(image_file)
        top, right, bottom, left = face_location
        face_image = face_image[top:bottom, left:right]
        pil_image = Image.fromarray(face_image)
        blob = BytesIO()
        pil_image.save(blob, "jpeg")
        return blob


class PhotoService:
    def delete_photo(self, photo_pk):
        photo = Photo.objects.get(pk=photo_pk)
        photo.photo_raw.delete()
        photo.photo_high.delete()
        photo.photo_medium.delete()
        photo.photo_thumb.delete()
        photo.delete()

    def extract_zip_file(self, photozip):
        photo_images = []
        extracted_path = os.path.splitext(photozip)[0]
        with ZipFile(photozip, "r") as zippedImgs:
            for filename in zippedImgs.namelist():
                if "MACOSX" not in filename and (".jpg" in filename or ".JPG"):
                    zippedImgs.extract(filename, path=extracted_path)
                    photo_images.append(os.path.join(extracted_path, filename))
        os.remove(photozip)
        return photo_images

    def process_photo(self, photo_path, user):
        photo_name = os.path.basename(photo_path)
        image_raw = File(open(photo_path, "rb"))
        photo = Photo(description=photo_name, author=user)
        photo.save()
        photo.photo_raw.save(photo_name, image_raw)
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
        photo.save()
        os.remove(photo_path)
        if not os.listdir(os.path.dirname(photo_path)):
            os.rmdir(os.path.dirname(photo_path))

        return photo.id

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

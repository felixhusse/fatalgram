from django.conf import settings
from django.db import models
from django.utils import timezone


def path_raw(instance, filename):
    return f"gallery/user_{instance.author.username}/raw/{filename}"


def path_highquality(instance, filename):
    return f"gallery/user_{instance.author.username}/hd/{filename}"


def path_mediumquality(instance, filename):
    return f"gallery/user_{instance.author.username}/md/{filename}"


def path_thumb(instance, filename):
    return f"gallery/user_{instance.author.username}/thumbs/{filename}"


def path_face_thumb(instance, filename):
    return f"gallery/user_{instance.person.author.username}/faces/{filename}"


class Trip(models.Model):
    title = models.CharField(max_length=50)
    trip_start = models.DateField(blank=True, null=True)
    trip_end = models.DateField(blank=True, null=True)
    summary = models.TextField()

    def publish(self):
        self.save()

    def __str__(self):
        return self.title


class Photo(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, blank=True, null=True, on_delete=models.SET_NULL)
    description = models.TextField()
    photo_taken = models.DateTimeField(blank=True, null=True)
    photo_camera = models.CharField(max_length=200, null=True)
    photo_lat = models.CharField(max_length=200, null=True)
    photo_lon = models.CharField(max_length=200, null=True)
    photo_alt = models.CharField(max_length=200, null=True)
    photo_raw = models.ImageField(upload_to=path_raw)
    photo_thumb = models.ImageField(upload_to=path_thumb)
    photo_high = models.ImageField(upload_to=path_highquality, null=True)
    photo_medium = models.ImageField(upload_to=path_mediumquality, null=True)
    upload_date = models.DateTimeField(default=timezone.now)

    def publish(self):
        self.save()

    def __str__(self):
        return self.description


class Person(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=200)
    photos = models.ManyToManyField("Photo", null=True)

    def publish(self):
        self.save()

    def __str__(self):
        return self.name


class PersonEncoding(models.Model):
    face_encoding = models.TextField()
    face_thumb = models.ImageField(upload_to=path_face_thumb)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def publish(self):
        self.save()

    def __str__(self):
        return self.person.name + f"_{self.id}"

import datetime

from django.shortcuts import render


def home(request):
    now = datetime.datetime.now()
    return render(request, "pages/home.html", {"time": now})

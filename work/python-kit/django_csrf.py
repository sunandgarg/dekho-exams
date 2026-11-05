from django.conf import settings
settings.configure(SECRET_KEY="owned-local-csrf-fixture", ROOT_URLCONF=__name__,
                   ALLOWED_HOSTS=["testserver"],
                   MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"], INSTALLED_APPS=[])
import django
django.setup()
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.urls import path
from django.test import Client

def review(request):
    get_token(request)
    return HttpResponse("local review received")

urlpatterns = [path("review/", review)]
client = Client(enforce_csrf_checks=True)
client.get("/review/")
token = client.cookies["csrftoken"].value
print("without token:", client.post("/review/", {}).status_code)
print("with token:", client.post("/review/", {}, HTTP_X_CSRFTOKEN=token).status_code)

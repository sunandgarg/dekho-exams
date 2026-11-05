from django.conf import settings
settings.configure(SECRET_KEY="local-fixture-only", DEBUG=False, ROOT_URLCONF=__name__,
                   ALLOWED_HOSTS=["testserver"], INSTALLED_APPS=[], MIDDLEWARE=[])
import django
django.setup()
from django.http import JsonResponse
from django.test import Client
from django.urls import path

def receipt(request, receipt_id):
    if receipt_id <= 0:
        return JsonResponse({"error": "positive ID required"}, status=400)
    return JsonResponse({"receipt_id": receipt_id, "amount_minor": 125})

urlpatterns = [path("receipts/<int:receipt_id>/", receipt)]
client = Client()
response = client.get("/receipts/41/")
print(response.status_code, response.json())
print(client.get("/receipts/0/").status_code)
print(client.get("/receipts/missing/").status_code)

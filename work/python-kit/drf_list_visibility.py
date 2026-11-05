from types import SimpleNamespace
from django.conf import settings
settings.configure(INSTALLED_APPS=[], SECRET_KEY="owned-list-fixture", REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES": [], "UNAUTHENTICATED_USER": None})
import django
django.setup()
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory, force_authenticate

RECEIPTS = [{"id": 41, "owner_id": 7}, {"id": 42, "owner_id": 8}, {"id": 43, "owner_id": 7}, {"id": 44, "owner_id": 7}]
def visible_receipts(principal, after, limit):
    if type(principal) is not int or principal <= 0 or type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 2:
        raise ValueError("list boundary rejected")
    candidates = sorted((record for record in RECEIPTS if record["owner_id"] == principal and record["id"] > after), key=lambda record: record["id"])
    return [{"id": record["id"]} for record in candidates[:limit]]

class ReceiptList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(visible_receipts(request.user.pk, 0, 2))

request = APIRequestFactory().get("/receipts")
force_authenticate(request, user=SimpleNamespace(pk=7, is_authenticated=True))
print("owner page:", ReceiptList.as_view()(request).data)
print("next owner page:", visible_receipts(7, 43, 2))
print("other owner page:", visible_receipts(8, 0, 2))
print("anonymous:", ReceiptList.as_view()(APIRequestFactory().get("/receipts")).status_code)

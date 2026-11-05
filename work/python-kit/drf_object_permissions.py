from types import SimpleNamespace
from django.conf import settings
settings.configure(INSTALLED_APPS=[], SECRET_KEY="owned-local-permission-fixture",
                   REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES": [], "UNAUTHENTICATED_USER": None})
import django
django.setup()
from django.http import Http404
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory, force_authenticate

RECEIPTS = {41: {"receipt_id": "R-0041", "owner_id": 7}}
class ReceiptOwner(BasePermission):
    def has_object_permission(self, request, view, receipt):
        return receipt["owner_id"] == request.user.pk

class ReceiptView(APIView):
    permission_classes = [IsAuthenticated, ReceiptOwner]
    def get(self, request, number):
        receipt = RECEIPTS.get(number)
        if receipt is None:
            raise Http404
        self.check_object_permissions(request, receipt)
        return Response({"receipt_id": receipt["receipt_id"]})

def local_response(principal_id, number):
    request = APIRequestFactory().get(f"/receipts/{number}")
    if principal_id is not None:
        force_authenticate(request, user=SimpleNamespace(pk=principal_id, is_authenticated=True))
    return ReceiptView.as_view()(request, number=number).status_code

print("owner:", local_response(7, 41))
print("other user:", local_response(8, 41))
print("missing record:", local_response(7, 99))
print("anonymous:", local_response(None, 41))

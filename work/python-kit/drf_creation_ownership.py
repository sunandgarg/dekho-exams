from types import SimpleNamespace
from django.conf import settings
settings.configure(INSTALLED_APPS=[], USE_I18N=False, SECRET_KEY="owned-create-fixture", REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES": [], "UNAUTHENTICATED_USER": None})
import django
django.setup()
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory, force_authenticate

RECEIPTS = {}
class ExactAmount(serializers.Field):
    def to_internal_value(self, value):
        if type(value) is not int or not 0 <= value <= 1000000: raise serializers.ValidationError("amount rejected")
        return value
class ReceiptCreation(serializers.Serializer):
    receipt_id = serializers.RegexField(r"\AR-[0-9]{4}\Z", trim_whitespace=False)
    amount = ExactAmount()
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != {"receipt_id", "amount"}: raise serializers.ValidationError({"non_field_errors": ["fields rejected"]})
        return super().to_internal_value(data)
    def create(self, accepted):
        RECEIPTS[accepted["receipt_id"]] = accepted.copy()
        return accepted
class ReceiptCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ReceiptCreation(data=request.data); serializer.is_valid(raise_exception=True)
        if serializer.validated_data["receipt_id"] in RECEIPTS: return Response({"error": "duplicate"}, status=409)
        accepted = serializer.save(owner_id=request.user.pk)
        return Response({"receipt_id": accepted["receipt_id"]}, status=201)

def local_create(payload):
    request = APIRequestFactory().post("/receipts", payload, format="json")
    force_authenticate(request, user=SimpleNamespace(pk=7, is_authenticated=True))
    return ReceiptCreateView.as_view()(request).status_code

print("created:", local_create({"receipt_id": "R-0041", "amount": 125}))
print("assigned owner:", RECEIPTS["R-0041"]["owner_id"])
print("spoof rejected:", local_create({"receipt_id": "R-0042", "amount": 250, "owner_id": 8}))
print("retained records:", len(RECEIPTS))

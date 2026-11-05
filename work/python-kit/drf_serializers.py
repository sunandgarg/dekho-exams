from django.conf import settings
settings.configure(INSTALLED_APPS=[], USE_I18N=False)
import django
django.setup()
from rest_framework import serializers

class MinorAmount(serializers.Field):
    def to_internal_value(self, value):
        if type(value) is not int or not 0 <= value <= 1000000:
            raise serializers.ValidationError("exact bounded integer required")
        return value
    def to_representation(self, value):
        return value

class ReceiptInput(serializers.Serializer):
    receipt_id = serializers.RegexField(r"\AR-[0-9]{4}\Z", max_length=6, trim_whitespace=False)
    amount = MinorAmount()
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != {"receipt_id", "amount"}:
            raise serializers.ValidationError({"non_field_errors": ["exact field set required"]})
        return super().to_internal_value(data)

accepted = ReceiptInput(data={"receipt_id": "R-0041", "amount": 125})
accepted.is_valid(raise_exception=True)
print(dict(accepted.validated_data))
for amount in (True, "125", -1):
    candidate = ReceiptInput(data={"receipt_id": "R-0041", "amount": amount})
    print("accepted:", candidate.is_valid())
extra = ReceiptInput(data={"receipt_id": "R-0041", "amount": 125, "owner_id": 41})
print("extra accepted:", extra.is_valid())

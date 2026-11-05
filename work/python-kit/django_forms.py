from django.conf import settings
settings.configure(SECRET_KEY="local-fixture-only", USE_I18N=False, INSTALLED_APPS=[])
import django
django.setup()
from django import forms

class ReceiptAmountForm(forms.Form):
    amount_minor = forms.RegexField(regex=r"\A[0-9]{1,6}\Z", max_length=6)
    def clean_amount_minor(self):
        amount = int(self.cleaned_data["amount_minor"])
        if amount == 0:
            raise forms.ValidationError("positive amount required")
        return amount
    def clean(self):
        cleaned = super().clean()
        if set(self.data) != {"amount_minor"}:
            raise forms.ValidationError("unexpected fields")
        return cleaned

accepted = ReceiptAmountForm({"amount_minor": "125"})
print(accepted.is_valid(), accepted.cleaned_data)
print(ReceiptAmountForm({"amount_minor": "１２５"}).is_valid())
print(ReceiptAmountForm({"amount_minor": "125", "owner": "other"}).is_valid())

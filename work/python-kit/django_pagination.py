from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                   DEFAULT_AUTO_FIELD="django.db.models.AutoField", USE_TZ=True)
import django
django.setup()
from django.db import connection, models, IntegrityError, transaction

class DispatchPartner(models.Model):
    region = models.CharField(max_length=3, unique=True)
    class Meta:
        app_label = "receipt_fixture"

class StoredReceipt(models.Model):
    receipt_id = models.CharField(max_length=6, unique=True)
    partner = models.ForeignKey(DispatchPartner, on_delete=models.PROTECT)
    amount = models.IntegerField()
    class Meta:
        app_label = "receipt_fixture"
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=0), name="receipt_amount_nonnegative")]

with connection.schema_editor() as schema:
    schema.create_model(DispatchPartner)
    schema.create_model(StoredReceipt)

def receipt_page(after_id=0, size=2):
    if type(after_id) is not int or after_id < 0 or type(size) is not int or not 1 <= size <= 20:
        raise ValueError("invalid page request")
    selected = list(StoredReceipt.objects.filter(id__gt=after_id).order_by("id").values_list("id", flat=True)[:size + 1])
    page = selected[:size]
    cursor = page[-1] if len(selected) > size else None
    return page, cursor

partner = DispatchPartner.objects.create(region="DEL")
for number in (41, 42, 43):
    StoredReceipt.objects.create(receipt_id=f"R-{number:04d}", partner=partner, amount=125)
first, cursor = receipt_page()
print(first, cursor)
print(receipt_page(cursor))
try:
    receipt_page(True)
except ValueError:
    print("boolean cursor rejected")
connection.close()

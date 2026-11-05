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

from django.test.utils import CaptureQueriesContext
partner = DispatchPartner.objects.create(region="DEL")
for number in (41, 42, 43):
    StoredReceipt.objects.create(receipt_id=f"R-{number:04d}", partner=partner, amount=125)
with CaptureQueriesContext(connection) as plain_queries:
    plain = [receipt.partner.region for receipt in StoredReceipt.objects.order_by("id")]
with CaptureQueriesContext(connection) as joined_queries:
    joined = [receipt.partner.region for receipt in StoredReceipt.objects.select_related("partner").order_by("id")]
print("same regions:", plain == joined)
print("plain queries:", len(plain_queries))
print("joined queries:", len(joined_queries))
connection.close()

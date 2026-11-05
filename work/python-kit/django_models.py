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

partner = DispatchPartner.objects.create(region="DEL")
StoredReceipt.objects.create(receipt_id="R-0041", partner=partner, amount=125)
try:
    with transaction.atomic():
        StoredReceipt.objects.create(receipt_id="R-0042", partner=partner, amount=-1)
except IntegrityError:
    print("database constraint rejected negative amount")
print("stored receipts:", StoredReceipt.objects.count())
connection.close()

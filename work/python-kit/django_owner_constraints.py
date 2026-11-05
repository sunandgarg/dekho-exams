from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}, DEFAULT_AUTO_FIELD="django.db.models.AutoField")
import django
django.setup()
from django.db import connection, models, transaction, IntegrityError

class OwnedReceipt(models.Model):
    owner_id = models.PositiveIntegerField()
    receipt_id = models.CharField(max_length=6)
    amount = models.IntegerField()
    class Meta:
        app_label = "owned_receipt_fixture"
        constraints = [models.UniqueConstraint(fields=["owner_id", "receipt_id"], name="owner_receipt_identity"),
                       models.CheckConstraint(condition=models.Q(amount__gte=0), name="owned_amount_nonnegative")]

with connection.schema_editor() as schema:
    schema.create_model(OwnedReceipt)
try:
    OwnedReceipt.objects.create(owner_id=1, receipt_id="R-0041", amount=125)
    OwnedReceipt.objects.create(owner_id=2, receipt_id="R-0041", amount=250)
    try:
        with transaction.atomic():
            OwnedReceipt.objects.create(owner_id=1, receipt_id="R-0041", amount=500)
    except IntegrityError:
        print("same-owner duplicate rejected")
    try:
        with transaction.atomic():
            OwnedReceipt.objects.bulk_create([OwnedReceipt(owner_id=1, receipt_id="R-0042", amount=-1)])
    except IntegrityError:
        print("bulk negative amount rejected")
    print("stored:", list(OwnedReceipt.objects.order_by("owner_id").values_list("owner_id", "amount")))
finally:
    connection.close()

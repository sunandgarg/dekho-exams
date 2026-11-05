from pathlib import Path
from io import StringIO
import importlib
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    package = Path(directory) / "receipt_store"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "models.py").write_text(
        'from django.db import models\n'
        'class Receipt(models.Model):\n'
        '    receipt_id = models.CharField(max_length=6, unique=True)\n', encoding="utf-8")
    sys.path.insert(0, directory)
    from django.conf import settings
    settings.configure(INSTALLED_APPS=["receipt_store"],
                       DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                       DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.loader import MigrationLoader
    with StringIO() as command_output:
        call_command("makemigrations", "receipt_store", verbosity=0, stdout=command_output)
        call_command("migrate", verbosity=0, stdout=command_output)
    Receipt = importlib.import_module("receipt_store.models").Receipt
    Receipt.objects.create(receipt_id="R-0041")
    print("initial migration written:", (package / "migrations" / "0001_initial.py").exists())
    print("initial migration applied:", ("receipt_store", "0001_initial") in MigrationLoader(connection).applied_migrations)
    print("stored records:", Receipt.objects.count())
    connection.close()
    sys.path.remove(directory)

class ReceiptExporter:
    def render(self, identifier):
        raise NotImplementedError("export format required")

class JsonReceiptExporter(ReceiptExporter):
    def render(self, identifier):
        import json
        return json.dumps({"receipt_id": identifier}, sort_keys=True)

def export_receipt(exporter, identifier):
    return exporter.render(identifier)

print(export_receipt(JsonReceiptExporter(), 41))

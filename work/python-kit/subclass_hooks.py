class ReceiptParser:
    def __init_subclass__(cls, *, wire_name=None, **options):
        super().__init_subclass__(**options)
        if not isinstance(wire_name, str) or not wire_name or len(wire_name) > 32:
            raise ValueError("wire name required")
        cls.wire_name = wire_name

class MinorParser(ReceiptParser, wire_name="receipt-minor"):
    pass

print(MinorParser.wire_name)
try:
    class UnnamedParser(ReceiptParser):
        pass
except ValueError:
    print("unnamed declaration rejected")

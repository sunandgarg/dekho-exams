class ImportSession:
    def __init__(self):
        self.rejected_ids = []

    def reject(self, receipt_id):
        self.rejected_ids.append(receipt_id)

first_session = ImportSession()
second_session = ImportSession()
first_session.reject("R41")
print(first_session.rejected_ids)
print(second_session.rejected_ids)

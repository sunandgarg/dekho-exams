class PageRedoJournal:
    def __init__(self, checkpoint_pages):
        self.checkpoint_pages = dict(checkpoint_pages)
        self.records = []
        self.next_transaction = 47

    def record(self, page_changes, commit=True):
        transaction = self.next_transaction
        self.next_transaction += 1
        self.records.append(("begin", transaction))
        for page_id, contents in page_changes.items():
            self.records.append(("page", transaction, page_id, contents))
        if commit:
            self.records.append(("commit", transaction))
        return transaction

    def recover(self):
        pages = dict(self.checkpoint_pages)
        pending = {}
        for record in self.records:
            action, transaction, *details = record
            if action == "begin":
                pending[transaction] = {}
            elif action == "page":
                if transaction not in pending:
                    raise ValueError("page record without begin")
                page_id, contents = details
                pending[transaction][page_id] = contents
            elif action == "commit":
                if transaction not in pending:
                    raise ValueError("commit record without begin")
                pages.update(pending.pop(transaction))
            else:
                raise ValueError("unknown journal record")
        return pages


journal = PageRedoJournal({"P-19": "original"})
journal.record({"P-19": "rebalanced", "P-26": "new leaf"})
journal.record({"P-52": "unfinished split"}, commit=False)
print(journal.recover())

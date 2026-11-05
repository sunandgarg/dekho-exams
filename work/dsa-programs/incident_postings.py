from collections import defaultdict


class IncidentPostings:
    def __init__(self, documents):
        self.postings = defaultdict(list)
        for document_id in sorted(documents):
            for term in set(documents[document_id]):
                self.postings[term].append(document_id)

    @staticmethod
    def _intersect(left, right):
        matched = []
        left_at = right_at = 0
        while left_at < len(left) and right_at < len(right):
            if left[left_at] == right[right_at]:
                matched.append(left[left_at])
                left_at += 1
                right_at += 1
            elif left[left_at] < right[right_at]:
                left_at += 1
            else:
                right_at += 1
        return matched

    def containing_all(self, terms):
        unique_terms = list(dict.fromkeys(terms))
        if not unique_terms:
            return []
        lists = [self.postings.get(term, []) for term in unique_terms]
        lists.sort(key=len)
        matched = lists[0][:]
        for posting_list in lists[1:]:
            matched = self._intersect(matched, posting_list)
            if not matched:
                break
        return matched


if __name__ == "__main__":
    incidents = IncidentPostings({
        103: ["valve", "pressure", "pressure"],
        218: ["pump", "pressure"],
        347: ["valve", "pressure", "pump"],
        492: ["valve", "sensor"],
    })
    print("valve-and-pressure=", incidents.containing_all(["valve", "pressure"]), sep="")
    print("valve-and-sensor=", incidents.containing_all(["valve", "sensor"]), sep="")
    print("missing=", incidents.containing_all(["valve", "offline"]), sep="")

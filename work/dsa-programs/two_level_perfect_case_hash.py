import random


PRIME = 1000003


class StaticCasePerfectHash:
    def __init__(self, case_ids):
        keys = sorted(set(case_ids))
        if any(key < 0 or key >= PRIME for key in keys):
            raise ValueError("case ID outside fixed prime field")
        self.count = len(keys)
        self.first_size = max(1, self.count)
        randomizer = random.Random(941)
        for _ in range(300):
            first_a = randomizer.randrange(1, PRIME)
            first_b = randomizer.randrange(PRIME)
            groups = [[] for _ in range(self.first_size)]
            for key in keys:
                groups[((first_a * key + first_b) % PRIME) % self.first_size].append(key)
            if sum(len(group) ** 2 for group in groups) <= max(1, 4 * self.count):
                break
        else:
            raise RuntimeError("first-level construction budget exhausted")
        self.first_a, self.first_b = first_a, first_b
        self.second = []
        for group in groups:
            width = max(1, len(group) ** 2)
            for _ in range(500):
                multiplier = randomizer.randrange(1, PRIME)
                offset = randomizer.randrange(PRIME)
                slots = [None] * width
                for key in group:
                    position = ((multiplier * key + offset) % PRIME) % width
                    if slots[position] is not None:
                        break
                    slots[position] = key
                else:
                    self.second.append((multiplier, offset, slots))
                    break
            else:
                raise RuntimeError("second-level construction budget exhausted")

    def contains(self, case_id):
        if not 0 <= case_id < PRIME:
            return False
        first = ((self.first_a * case_id + self.first_b) % PRIME) % self.first_size
        multiplier, offset, slots = self.second[first]
        second = ((multiplier * case_id + offset) % PRIME) % len(slots)
        return slots[second] == case_id

    def allocated_slots(self):
        return sum(len(slots) for _, _, slots in self.second)


if __name__ == "__main__":
    index = StaticCasePerfectHash([19, 29, 47, 61, 83, 103, 127])
    print("stored:", index.count, "slots:", index.allocated_slots())
    print("has 61:", index.contains(61))
    print("has 62:", index.contains(62))

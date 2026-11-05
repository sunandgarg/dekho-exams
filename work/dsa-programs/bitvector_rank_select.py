"""Static rank/select over a packed incident-state bitmap."""

from bisect import bisect_right


class IncidentBitmap:
    WORD_BITS = 64

    def __init__(self, active_flags: list[bool]):
        self.length = len(active_flags)
        self.words = [0] * ((self.length + self.WORD_BITS - 1) // self.WORD_BITS)
        for position, active in enumerate(active_flags):
            if active:
                self.words[position // self.WORD_BITS] |= 1 << (position % self.WORD_BITS)
        self.ones_before_word = [0]
        for word in self.words:
            self.ones_before_word.append(self.ones_before_word[-1] + word.bit_count())

    def rank1(self, stop: int) -> int:
        if not 0 <= stop <= self.length:
            raise IndexError(stop)
        word_number, offset = divmod(stop, self.WORD_BITS)
        count = self.ones_before_word[word_number]
        if offset:
            count += (self.words[word_number] & ((1 << offset) - 1)).bit_count()
        return count

    def select1(self, ordinal: int) -> int:
        if not 0 <= ordinal < self.ones_before_word[-1]:
            raise IndexError(ordinal)
        word_number = bisect_right(self.ones_before_word, ordinal) - 1
        remaining = ordinal - self.ones_before_word[word_number]
        word = self.words[word_number]
        while remaining:
            word &= word - 1
            remaining -= 1
        lowest_bit = word & -word
        return word_number * self.WORD_BITS + lowest_bit.bit_length() - 1


incident_bitmap = IncidentBitmap([False] * 19 + [True] + [False] * 27 + [True] + [False] * 13 + [True])
print(incident_bitmap.rank1(48))
print(incident_bitmap.select1(1))
print(incident_bitmap.rank1(incident_bitmap.length))

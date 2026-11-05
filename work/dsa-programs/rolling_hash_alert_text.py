class AlertTextFingerprint:
    BASE = 911382323
    MODULI = (1000000007, 1000000009)

    def __init__(self, alert_text):
        if not alert_text:
            raise ValueError("at least one character is required")
        self.length = len(alert_text)
        self.powers = [[1] * (self.length + 1) for _ in self.MODULI]
        for number, modulus in enumerate(self.MODULI):
            for count in range(1, self.length + 1):
                self.powers[number][count] = self.powers[number][count - 1] * self.BASE % modulus
        self.tree = [None] * (4 * self.length)

        def build(node, low, high):
            if high - low == 1:
                encoded = ord(alert_text[low]) + 1
                self.tree[node] = (1, encoded % self.MODULI[0], encoded % self.MODULI[1])
                return
            middle = (low + high) // 2
            build(node * 2, low, middle)
            build(node * 2 + 1, middle, high)
            self.tree[node] = self._join(self.tree[node * 2], self.tree[node * 2 + 1])

        build(1, 0, self.length)

    def _join(self, left, right):
        if left is None:
            return right
        if right is None:
            return left
        return (left[0] + right[0],
                (left[1] * self.powers[0][right[0]] + right[1]) % self.MODULI[0],
                (left[2] * self.powers[1][right[0]] + right[2]) % self.MODULI[1])

    def replace(self, position, character):
        if not 0 <= position < self.length or len(character) != 1:
            raise ValueError("one in-range character required")

        def change(node, low, high):
            if high - low == 1:
                encoded = ord(character) + 1
                self.tree[node] = (1, encoded % self.MODULI[0], encoded % self.MODULI[1])
                return
            middle = (low + high) // 2
            if position < middle:
                change(node * 2, low, middle)
            else:
                change(node * 2 + 1, middle, high)
            self.tree[node] = self._join(self.tree[node * 2], self.tree[node * 2 + 1])

        change(1, 0, self.length)

    def fingerprint(self, left, right):
        if not 0 <= left <= right <= self.length:
            raise IndexError("invalid text interval")

        def read(node, low, high):
            if right <= low or high <= left:
                return None
            if left <= low and high <= right:
                return self.tree[node]
            middle = (low + high) // 2
            return self._join(read(node * 2, low, middle), read(node * 2 + 1, middle, high))

        return read(1, 0, self.length) or (0, 0, 0)

    def possibly_equal(self, first, second, width):
        if width < 0:
            raise ValueError("negative width")
        return self.fingerprint(first, first + width) == self.fingerprint(second, second + width)


alert_text = AlertTextFingerprint("dock47dock47")
print(alert_text.possibly_equal(0, 6, 6), alert_text.possibly_equal(0, 6, 4))
alert_text.replace(11, "9")
print(alert_text.possibly_equal(0, 6, 6))
alert_text.replace(11, "7")
print(alert_text.possibly_equal(0, 6, 6))

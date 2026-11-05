MODULUS = 97


def compose(first, second):
    """Apply first, then second, to a reading modulo MODULUS."""
    first_scale, first_shift = first
    second_scale, second_shift = second
    return (first_scale * second_scale % MODULUS,
            (first_shift * second_scale + second_shift) % MODULUS)


IDENTITY = (1, 0)


class CalibrationWindow:
    def __init__(self):
        self.front = []
        self.back = []

    def append(self, calibration):
        prior = self.back[-1][1] if self.back else IDENTITY
        self.back.append((calibration, compose(prior, calibration)))

    def remove_oldest(self):
        if not self.front:
            while self.back:
                calibration, _ = self.back.pop()
                prior = self.front[-1][1] if self.front else IDENTITY
                self.front.append((calibration, compose(calibration, prior)))
        if not self.front:
            raise IndexError("calibration window is empty")
        return self.front.pop()[0]

    def combined(self):
        left = self.front[-1][1] if self.front else IDENTITY
        right = self.back[-1][1] if self.back else IDENTITY
        return compose(left, right)


if __name__ == "__main__":
    window = CalibrationWindow()
    for calibration in [(2, 19), (3, 7), (5, 11)]:
        window.append(calibration)
    print("first:", window.combined())
    print("removed:", window.remove_oldest())
    window.append((7, 23))
    print("second:", window.combined())

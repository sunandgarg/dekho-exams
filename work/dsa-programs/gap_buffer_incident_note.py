class IncidentGapBuffer:
    def __init__(self, text="", gap_capacity=8):
        if gap_capacity < 1:
            raise ValueError("gap capacity must be positive")
        self.buffer = list(text) + [None] * gap_capacity
        self.gap_left = len(text)
        self.gap_right = len(self.buffer)

    def __len__(self):
        return len(self.buffer) - (self.gap_right - self.gap_left)

    def move_cursor(self, position):
        if not 0 <= position <= len(self):
            raise IndexError("cursor outside note")
        while self.gap_left > position:
            self.gap_left -= 1
            self.gap_right -= 1
            self.buffer[self.gap_right] = self.buffer[self.gap_left]
            self.buffer[self.gap_left] = None
        while self.gap_left < position:
            self.buffer[self.gap_left] = self.buffer[self.gap_right]
            self.buffer[self.gap_right] = None
            self.gap_left += 1
            self.gap_right += 1

    def _grow(self, required):
        spare = max(len(self.buffer), required, 8)
        self.buffer[self.gap_right:self.gap_right] = [None] * spare
        self.gap_right += spare

    def insert(self, text):
        if not text:
            return
        if self.gap_right - self.gap_left <= len(text):
            self._grow(len(text) - (self.gap_right - self.gap_left) + 1)
        for character in text:
            self.buffer[self.gap_left] = character
            self.gap_left += 1

    def delete_forward(self, count):
        if count < 0 or count > len(self.buffer) - self.gap_right:
            raise IndexError("forward deletion outside note")
        for offset in range(count):
            self.buffer[self.gap_right + offset] = None
        self.gap_right += count

    def backspace(self, count):
        if count < 0 or count > self.gap_left:
            raise IndexError("backspace outside note")
        self.gap_left -= count
        for offset in range(count):
            self.buffer[self.gap_left + offset] = None

    def text(self):
        return "".join(self.buffer[:self.gap_left] + self.buffer[self.gap_right:])


note = IncidentGapBuffer("Valve offline", gap_capacity=4)
note.move_cursor(5)
note.insert("-19")
note.move_cursor(len(note))
note.insert(" at bay 6")
note.move_cursor(0)
note.insert("Alert: ")
print("note=", note.text(), " cursor=", note.gap_left, sep="")

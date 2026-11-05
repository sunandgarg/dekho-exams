"""Text editor using immutable source buffers and a mutable piece sequence."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Piece:
    source: int
    start: int
    length: int


class IncidentNote:
    def __init__(self, original: str):
        self.buffers = [original, ""]
        self.pieces = [Piece(0, 0, len(original))] if original else []
        self.length = len(original)

    def _split_at(self, position: int) -> int:
        if not 0 <= position <= self.length:
            raise IndexError(position)
        offset = 0
        for piece_index, piece in enumerate(self.pieces):
            next_offset = offset + piece.length
            if position == offset:
                return piece_index
            if offset < position < next_offset:
                left_length = position - offset
                self.pieces[piece_index:piece_index + 1] = [
                    Piece(piece.source, piece.start, left_length),
                    Piece(piece.source, piece.start + left_length, piece.length - left_length),
                ]
                return piece_index + 1
            offset = next_offset
        return len(self.pieces)

    def insert(self, position: int, text: str) -> None:
        piece_index = self._split_at(position)
        if not text:
            return
        start = len(self.buffers[1])
        self.buffers[1] += text
        self.pieces.insert(piece_index, Piece(1, start, len(text)))
        self.length += len(text)

    def delete(self, start: int, stop: int) -> None:
        if not 0 <= start <= stop <= self.length:
            raise IndexError((start, stop))
        first = self._split_at(start)
        last = self._split_at(stop)
        del self.pieces[first:last]
        self.length -= stop - start

    def text(self) -> str:
        return "".join(self.buffers[piece.source][piece.start:piece.start + piece.length]
                       for piece in self.pieces)


note = IncidentNote("Depot D-19 cleared")
note.insert(6, "north ")
note.delete(12, 17)
print(note.text())
print(note.length)
print(len(note.pieces))

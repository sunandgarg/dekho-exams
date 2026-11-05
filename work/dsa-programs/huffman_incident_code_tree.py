from collections import Counter
from heapq import heappop, heappush


class CodeNode:
    def __init__(self, symbol=None, left=None, right=None):
        self.symbol, self.left, self.right = symbol, left, right


class IncidentCodebook:
    def __init__(self, training_text):
        frequencies = Counter(training_text)
        if not frequencies:
            raise ValueError("training text must contain a symbol")
        heap = []
        serial = 0
        for symbol, count in sorted(frequencies.items()):
            heappush(heap, (count, serial, CodeNode(symbol=symbol)))
            serial += 1
        while len(heap) > 1:
            left_count, _, left = heappop(heap)
            right_count, _, right = heappop(heap)
            heappush(heap, (left_count + right_count, serial, CodeNode(left=left, right=right)))
            serial += 1
        self.root = heap[0][2]
        self.codes = {}

        def assign(node, bits):
            if node.symbol is not None:
                self.codes[node.symbol] = bits or "0"
                return
            assign(node.left, bits + "0")
            assign(node.right, bits + "1")

        assign(self.root, "")

    def encode(self, text):
        return "".join(self.codes[symbol] for symbol in text)

    def decode(self, bits):
        if any(bit not in "01" for bit in bits):
            raise ValueError("nonbinary input")
        if self.root.symbol is not None:
            if any(bit != "0" for bit in bits):
                raise ValueError("invalid one-symbol code")
            return self.root.symbol * len(bits)
        output, cursor = [], self.root
        for bit in bits:
            cursor = cursor.left if bit == "0" else cursor.right
            if cursor.symbol is not None:
                output.append(cursor.symbol)
                cursor = self.root
        if cursor is not self.root:
            raise ValueError("incomplete final codeword")
        return "".join(output)


if __name__ == "__main__":
    training = "dispatch dispatch urgent"
    book = IncidentCodebook(training)
    payload = "dispatch urgent"
    bits = book.encode(payload)
    print(len(book.codes), len(bits))
    print(book.decode(bits))

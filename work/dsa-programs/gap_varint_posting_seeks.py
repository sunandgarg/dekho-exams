from bisect import bisect_right


def encode_unsigned(value):
    if value < 0:
        raise ValueError("negative gap")
    encoded = bytearray()
    while value >= 128:
        encoded.append((value & 127) | 128)
        value >>= 7
    encoded.append(value)
    return encoded


def decode_unsigned(data, offset):
    value = 0
    shift = 0
    while offset < len(data):
        part = data[offset]
        offset += 1
        value |= (part & 127) << shift
        if not part & 128:
            return value, offset
        shift += 7
    raise ValueError("truncated integer code")


class GapPostingIndex:
    def __init__(self, document_ids, checkpoint_stride=3):
        if checkpoint_stride < 1 or any(document_id < 0 for document_id in document_ids):
            raise ValueError("invalid document ID or stride")
        if any(left >= right for left, right in zip(document_ids, document_ids[1:])):
            raise ValueError("document IDs must increase strictly")
        self.data = bytearray()
        self.checkpoints = []
        self.checkpoint_ids = []
        self.count = len(document_ids)
        previous = 0
        for position, document_id in enumerate(document_ids):
            self.data.extend(encode_unsigned(document_id - previous))
            previous = document_id
            if position % checkpoint_stride == 0:
                self.checkpoints.append((document_id, len(self.data)))
                self.checkpoint_ids.append(document_id)

    def values(self):
        result = []
        previous = 0
        offset = 0
        while offset < len(self.data):
            gap, offset = decode_unsigned(self.data, offset)
            previous += gap
            result.append(previous)
        return result

    def seek_at_least(self, target):
        checkpoint = bisect_right(self.checkpoint_ids, target) - 1
        if checkpoint >= 0:
            previous, offset = self.checkpoints[checkpoint]
            if previous == target:
                return previous
        else:
            previous, offset = 0, 0
        while offset < len(self.data):
            gap, offset = decode_unsigned(self.data, offset)
            previous += gap
            if previous >= target:
                return previous
        return None


postings = GapPostingIndex([47, 61, 83, 129, 515], checkpoint_stride=2)
print("seek-80=", postings.seek_at_least(80), " seek-200=", postings.seek_at_least(200),
      " bytes=", len(postings.data), sep="")

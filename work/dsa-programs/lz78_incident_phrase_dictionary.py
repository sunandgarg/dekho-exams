class PhraseNode:
    def __init__(self, phrase_id):
        self.phrase_id = phrase_id
        self.children = {}


def encode_incident(text):
    root = PhraseNode(0)
    next_id = 1
    encoded = []
    position = 0
    while position < len(text):
        cursor = root
        while position < len(text) and text[position] in cursor.children:
            cursor = cursor.children[text[position]]
            position += 1
        if position == len(text):
            encoded.append((cursor.phrase_id, ""))
            break
        symbol = text[position]
        encoded.append((cursor.phrase_id, symbol))
        cursor.children[symbol] = PhraseNode(next_id)
        next_id += 1
        position += 1
    return encoded


def decode_incident(encoded):
    phrases = [""]
    output = []
    for position, (phrase_id, symbol) in enumerate(encoded):
        if not 0 <= phrase_id < len(phrases) or len(symbol) > 1:
            raise ValueError("invalid phrase token")
        if symbol == "" and (phrase_id == 0 or position != len(encoded) - 1):
            raise ValueError("only final nonempty phrase may omit symbol")
        phrase = phrases[phrase_id] + symbol
        output.append(phrase)
        if symbol:
            phrases.append(phrase)
    return "".join(output)


if __name__ == "__main__":
    incident = "cabacabacaba"
    tokens = encode_incident(incident)
    print(tokens)
    print(decode_incident(tokens))

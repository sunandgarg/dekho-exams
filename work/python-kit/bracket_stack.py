def balanced_brackets(text):
    if len(text) > 4096:
        raise ValueError("expression too long")
    closing = {"(": ")", "[": "]", "{": "}"}
    expected = []
    for token in text:
        if token in closing:
            expected.append(closing[token])
        elif token in ")]}":
            if not expected or expected.pop() != token:
                return False
        else:
            raise ValueError("brackets only")
    return not expected

print(balanced_brackets("{[()]}"))
print(balanced_brackets("([)]"))
print(balanced_brackets("(("))

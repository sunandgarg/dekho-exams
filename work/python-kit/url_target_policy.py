from urllib.parse import urlsplit

def accepted_target(text):
    if type(text) is not str or not 1 <= len(text) <= 128 or any(not 33 <= ord(char) <= 126 for char in text):
        raise ValueError("ASCII target bound")
    parsed = urlsplit(text)
    if (parsed.scheme != "https" or parsed.hostname != "learn.aitrove.in" or
        parsed.username is not None or parsed.password is not None or
        parsed.port not in (None, 443) or parsed.path != "/receipts" or
        parsed.query or parsed.fragment):
        raise ValueError("target policy")
    return "https://learn.aitrove.in/receipts"

print(accepted_target("https://learn.aitrove.in:443/receipts"))
for target in ("https://learn.aitrove.in.evil/receipts",
               "https://user@learn.aitrove.in/receipts", "\nhttps://learn.aitrove.in/receipts"):
    try:
        accepted_target(target)
    except ValueError:
        print("target rejected")

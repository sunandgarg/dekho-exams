def parse_amount(text):
    events = []
    try:
        amount = int(text)
    except ValueError:
        events.append("rejected")
        amount = None
    else:
        events.append("parsed")
    finally:
        events.append("cleanup")
    return amount, events

print(parse_amount("125"))
print(parse_amount("bad"))

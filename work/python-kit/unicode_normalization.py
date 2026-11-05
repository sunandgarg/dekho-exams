import unicodedata

stored_label = "Caf\u00e9"
imported_label = "Cafe\u0301"
print(stored_label == imported_label)
print(len(stored_label), len(imported_label))
print(unicodedata.normalize("NFC", stored_label) ==
      unicodedata.normalize("NFC", imported_label))

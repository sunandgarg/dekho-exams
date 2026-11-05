def longest_label_palindrome(text):
    if not isinstance(text, str) or len(text) > 128:
        raise ValueError("bounded label required")
    best_left = 0; best_right = 0
    for center in range(2 * len(text) - 1):
        left = center // 2; right = left + center % 2
        while left >= 0 and right < len(text) and text[left] == text[right]:
            if right + 1 - left > best_right - best_left:
                best_left, best_right = left, right + 1
            left -= 1; right += 1
    return text[best_left:best_right]

print(longest_label_palindrome("DELLEVELBOM"))
print(longest_label_palindrome("ABBA"))
print("empty:", repr(longest_label_palindrome("")))
print("leftmost tie:", longest_label_palindrome("ABACDC"))

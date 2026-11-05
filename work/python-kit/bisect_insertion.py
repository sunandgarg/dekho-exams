from bisect import bisect_left, bisect_right, insort_right

amounts = [75, 125, 125, 250]
print(bisect_left(amounts, 125), bisect_right(amounts, 125))
insort_right(amounts, 125)
print(amounts)
print("outside upper boundary:", bisect_right(amounts, 500))

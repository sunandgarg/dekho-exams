def maximum_window(amounts, width):
    if not 1 <= len(amounts) <= 128 or any(type(amount) is not int for amount in amounts):
        raise ValueError("bounded integer batch required")
    if type(width) is not int or not 1 <= width <= len(amounts):
        raise ValueError("window width rejected")
    running = sum(amounts[:width]); best = running
    for index in range(width, len(amounts)):
        running += amounts[index] - amounts[index - width]
        best = max(best, running)
    return best

amounts = [125, -50, 250, 75]
print(maximum_window(amounts, 2))
print("direct answer:", max(sum(amounts[index:index + 2]) for index in range(len(amounts) - 1)))
print("negative answer:", maximum_window([-5, -3], 1))
try:
    maximum_window(amounts, 0)
except ValueError:
    print("zero width rejected")

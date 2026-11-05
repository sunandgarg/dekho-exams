labels = [f"R{index}" for index in range(3)]
late = [lambda: index for index in range(3)]
bound = [lambda index=index: index for index in range(3)]
print(labels)
print("leaked:", "index" in globals())
print("late:", [callback() for callback in late])
print("bound:", [callback() for callback in bound])

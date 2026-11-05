adjustment = -7
package_size = 3
print(adjustment / package_size)
print(adjustment // package_size)
print(adjustment % package_size)
try:
    adjustment // 0
except ZeroDivisionError:
    print("zero divisor rejected")

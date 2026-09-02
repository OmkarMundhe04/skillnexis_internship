numbers = [23, 45, 12, 67, 34, 89]

# Sort by last digit using lambda
numbers.sort(key=lambda x: x % 10)

print("Sorted by last digit:", numbers)


numbers = list(map(int, input("Enter numbers separated by spaces: ").split()))


largest = numbers[0]
smallest = numbers[0]


for num in numbers:
    if num > largest:
        largest = num
    if num < smallest:
        smallest = num


print("Numbers entered:", numbers)
print("Largest number:", largest)
print("Smallest number:", smallest)

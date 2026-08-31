n_terms = int(input("How many terms of the Fibonacci sequence would you like to print? "))

n1, n2 = 0, 1
count = 0


if n_terms <= 0:
    print("Please enter a positive integer greater than 0.")
elif n_terms == 1:
    print(f"Fibonacci sequence up to {n_terms} term:")
    print(n1)
else:
    print(f"Fibonacci sequence up to {n_terms} terms:")

    while count < n_terms:
        print(n1, end=" ")
        nth = n1 + n2
        n1 = n2
        n2 = nth
        count += 1
    print() 
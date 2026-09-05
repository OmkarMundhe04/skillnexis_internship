class Calculator:
    def __init__(self):
        pass
    def add(self,a,b):
        return a+b
    def sub(self,a,b):
        return a-b
    def multiply(self,a,b):
        return a*b
    def divide(self,a,b):
        if b==0:
            return "Error: Division by zero"
        return a/b
class1=Calculator()
while True:
    print("\n--- Calculator Menu ---")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    print("5. Exit")

    choice = input("Enter your choice: ")

    match choice:
        case "1":
            a = float(input("Enter first number: "))
            b = float(input("Enter second number: "))
            
            print(f"Result: {class1.add(a, b)}")

        case "2":
            a = float(input("Enter first number: "))
            b = float(input("Enter second number: "))
            
            print(f"Result: {class1.sub(a, b)}")

        case "3":
            a = float(input("Enter first number: "))
            b = float(input("Enter second number: "))
            print(f"Result: {class1.multiply(a, b)}")

        case "4":
            a = float(input("Enter first number: "))
            b = float(input("Enter second number: "))
            
            print(f"Result: {class1.divide(a, b)}")

        case "5":
            print("Exiting the calculator.")
            break

        case _:
            print("Invalid choice. Please try again.")
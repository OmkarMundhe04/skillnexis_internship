class Cal:
    def __init__(self):
        pass
    def add(self,a,b):
        try:
            return a+b
        except Exception as e:
            print(f"Error in addition of {a} and {b}:" ,e)
    def subtract(slef,a,b):
        try:
            return a - b
        except Exception as e:
            print("Error in subtraction : ",e)
    def multiply(slef,a,b):
        try:
            return a * b
        except Exception as e:
            print("Error in Multiplication : ",e)
    def divide(slef,a,b):
        try:
            return a / b
        except Exception as e:
            print("Error in division  : ",e)

cal1=Cal()
a=int(input("Enter the value for a : "))
b=int(input("Enter the value for b : "))
print(cal1.add(a,b))
print(cal1.subtract(a,b))
print(cal1.multiply(a,b))
print(cal1.divide(a,b))
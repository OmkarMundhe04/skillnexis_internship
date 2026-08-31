def fact(n):
	if n ==0 or n ==1:
		return 1
	else:
		return n*fact(n-1)
n=int(input("Enter the number to calculate its factorial : "))
if n<0:
	print("Factorial cant be calculated for negative numbers. ")
else:
	result=fact(n)
	print(f"The factorial for the given number {n} is {result}.")
class BankAccount:
    def __init__(self,owner,balance=0):
        self.owner=owner
        self.balance=balance
    def deposit(self,amount):
        if amount>0:
            self.balance += amount
            print(f"Deposited {amount} . New Balance : {self.balance}")
        else:
            print("Deposit amount must be positive ")
    def withdraw(self,amount):
        if amount> self.balance:
            print("Insufficient balance")
        elif amount <=0:
            print("Please enter a valid amount to withdraw")
        else:
            self.balance-=amount
            print(f"The withdrew {amount}. New balance: {self.balance}")

    def display_balance(self):
        print(f"The account owner {self.owner} has balance of Rs. {self.balance} ")

account1=BankAccount("omkar",1000)
account1.deposit(500)
account1.withdraw(200)
account1.display_balance()
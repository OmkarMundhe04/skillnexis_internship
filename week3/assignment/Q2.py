class Lib:
    def __init__(self,name):
        self.name=name
        self.books=[]
        self.issued_books={}
    def add_book(self,book):
        
        self.books.append(book)
        print(f"book {book} has been added to the library.")
    def remove_book(self,book):
        if book in self.books:
            self.books.remove(book)
            print(f"Book {book} removed from lib")
        else:
            print(f"Book named as {book} isnt found in lib")
    def issue_book(self,book,user):
        if book in self.books:
            self.books.remove(book)
            self.issued_books[book]=user
            print(f"Book {book} issued to {user}")
        else:
            print(f"Book {book} is not available")
    def return_book(self,book):
        if book in self.issued_books:
            user=self.issued_books.pop(book)
            self.books.append(book)
            print(f"Book {book} is returned by user {user}")
        else :
            print(f"Book named {book} was not issued to anyone")
    def display_books(self):
        print(f"\nBooks Availble in {self.name}:")
        if not self.books:
            print(f"No books found in the lib")
        else:
            for i,book in enumerate (self.books,start=1):
                print(f"{i}.{book}")
lib1 = Lib("Omkar's Lib")
no=int(input("Enter the number of books you want to add in lib: "))
for i in range(1,no+1):
    book=input("Enter the book name to add in lib: ")
    lib1.add_book(book)
lib1.display_books()
name=input("Enter the name of book to get issued : ")
user=input("Enter the name of user to whom book is issued: ")
lib1.issue_book(name,user)

lib1.display_books()

rem=input("Enter the book name to remove: ")
lib1.remove_book(rem)
lib1.display_books()
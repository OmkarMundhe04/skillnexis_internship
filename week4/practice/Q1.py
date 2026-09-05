class ContactBook:
    def __init__(self):
        self.contacts = {}

    def add_contact(self, name, phone):
        self.contacts[name] = phone
        print(f"✅ Contact {name} added.")

    def remove_contact(self, name):
        if name in self.contacts:
            del self.contacts[name]
            print(f"🗑️ Contact {name} removed.")
        else:
            print(f"❌ Contact {name} not found.")

    def search_contact(self, name):
        if name in self.contacts:
            print(f"🔎 Found: {name} - {self.contacts[name]}")
        else:
            print(f"❌ Contact {name} not found.")

    def display_contacts(self):
        if not self.contacts:
            print("📂 No contacts available.")
        else:
            print("\n📋 Contact List:")
            for name, phone in self.contacts.items():
                print(f"{name} - {phone}")


# ------------------ Menu-driven with match-case ------------------

book = ContactBook()

while True:
    print("\n--- Contact Book Menu ---")
    print("1. Add Contact")
    print("2. Remove Contact")
    print("3. Search Contact")
    print("4. Display Contacts")
    print("5. Exit")

    choice = input("Enter your choice: ")

    match choice:
        case "1":
            name = input("Enter name: ")
            phone = input("Enter phone number: ")
            book.add_contact(name, phone)

        case "2":
            name = input("Enter name to remove: ")
            book.remove_contact(name)

        case "3":
            name = input("Enter name to search: ")
            book.search_contact(name)

        case "4":
            book.display_contacts()

        case "5":
            print("📌 Exiting Contact Book. Goodbye!")
            break

        case _:
            print("⚠️ Invalid choice. Try again.")

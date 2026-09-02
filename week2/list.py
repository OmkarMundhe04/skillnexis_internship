

def show_menu():
    print("\n--- CRUD Menu ---")
    print("1. Create (Add item)")
    print("2. Read (View items)")
    print("3. Update (Modify item)")
    print("4. Delete (Remove item)")
    print("5. Exit")

# Initial empty list
items = []

while True:
    show_menu()
    choice = input("Enter your choice (1-5): ")

    if choice == "1":
        # Create
        new_item = input("Enter item to add: ")
        items.append(new_item)
        print(f"'{new_item}' added successfully!")

    elif choice == "2":
        # Read
        if items:
            print("\nCurrent items:")
            for i, item in enumerate(items, start=1):
                print(f"{i}. {item}")
        else:
            print("List is empty.")

    elif choice == "3":
        # Update
        if items:
            for i, item in enumerate(items, start=1):
                print(f"{i}. {item}")
            index = int(input("Enter item number to update: ")) - 1
            if 0 <= index < len(items):
                new_value = input("Enter new value: ")
                print(f"'{items[index]}' updated to '{new_value}'")
                items[index] = new_value
            else:
                print("Invalid index.")
        else:
            print("List is empty.")

    elif choice == "4":
        # Delete
        if items:
            for i, item in enumerate(items, start=1):
                print(f"{i}. {item}")
            index = int(input("Enter item number to delete: ")) - 1
            if 0 <= index < len(items):
                removed = items.pop(index)
                print(f"'{removed}' deleted successfully!")
            else:
                print("Invalid index.")
        else:
            print("List is empty.")

    elif choice == "5":
        print("Exiting program. Goodbye!")
        break

    else:
        print("Invalid choice. Please enter a number between 1 and 5.")

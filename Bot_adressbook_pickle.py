import re
import pickle
from collections import UserDict
from datetime import datetime

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name and number"
        except KeyError:
            return "Contact not found"
        except IndexError:
            return "Not found"
    return inner

def parse_input(user_input):
    cmd,*args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

@input_error
def add_contact(args, book):
    name, phone = args
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return "Contact added/updated."

@input_error
def change_contact(args, book):
    if len(args) != 2:
        raise ValueError
    name, phone = args
    if name in book:
        book[name] = phone
        return "Contact updated successfully"
    else:
        raise KeyError

@input_error
def phone_contact(args, book):
    if len(args) != 1:
        raise IndexError
    name = args[0]
    if name in book:
        return book[name]
    else:
        raise KeyError

@input_error   
def snow_all(book):
    if not book:
        return "No contacts found"
    return "\n".join([f"{name}: {phone}" for name, phone in book.items()])

@input_error
def add_birthday(args, book):
    if len(args) != 2:
        raise ValueError("Provide name and birthday in the format DD/MM/YYYY or DD.MM.YYYY")
    name, birthday = args
    record = book.find(name)
    if record:
        try:
            record.birthday = Birthday(birthday)  
            return "Birthday added successfully"
        except ValueError as e:
            return str(e)  
    else:
        raise KeyError(f"Contact {name} not found")

@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise IndexError("Provide exactly one name.")
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return record.birthday.value.strftime('%d/%m/%Y')  
    elif record:
        return f"{name} does not have a birthday set."
    else:
        raise KeyError(f"Contact {name} not found.")
    
@input_error
def show_all_birthdays(book):
    if not book:
        return "No birthdays found"
    result = []
    for name, record in book.items():
        if record.birthday:
            result.append(f"{name}: {record.birthday.value.strftime('%d/%m/%Y')}")
    return "\n".join(result) if result else "No birthdays found"

class  Field :
     def  __init__ ( self, value ):
        self.value = value
    
     def  __str__ ( self ):
        return  str (self.value)

class  Name ( Field ):
    pass

class  Phone ( Field ):
    def __init__ ( self, value ):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be exactly 10 digits.")
        super().__init__(value)
    pass

class  Birthday ( Field ):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            try:
                self.value = datetime.strptime(value, "%d.%m.%Y").date()
            except ValueError:
                raise ValueError("Invalid date format. Use DD/MM/YYYY or DD.MM.YYYY")

class  Record :
     def  __init__ ( self, name ):
        self.name = Name(name)
        self.phones = []
        self .birthday = None

     def  add_phone ( self, phone ):
        self.phones.append(Phone(phone))

     def  remove_phone ( self, phone ):
        self.phones.remove(Phone(phone))

     def edit_phone ( self, phone, new_phone ):
        self.phones.remove(Phone(phone))
        self.phones.append(Phone(new_phone))

     def find_phone ( self, phone ):
        for p in self.phones:
            if p.value == phone:
             return p
        return None   

     def  __str__ ( self ):
        phones = '; '.join(p.value for p in self.phones)
        birthday = f", birthday: {self.birthday.value.strftime('%d/%m/%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"
     
class AddressBook(UserDict):
    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())

    def  add_record ( self, record ):
        if not isinstance(record, Record):
            raise ValueError("Only Record instances can be added to the AddressBook.")
        self.data[record.name.value] = record
    
    def find ( self, name ):
        return self.data.get(name, None)

    def delete ( self, name ):
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError(f"Contact {name} not found.")
    
    def get_upcoming_birthdays(self, days):
        today = datetime.today()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                if (record.birthday.value - today).days <= days:
                    upcoming_birthdays.append(record)
        return upcoming_birthdays

    def save_to_file(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    @classmethod
    def load_from_file(cls, filename):
        try:
            with open(filename, 'rb') as file:
                return pickle.load(file)
        except FileNotFoundError:
            return cls()


def main():
    book = AddressBook.load_from_file("addressbook.pkl")
    print("Welcome to the assistant bot")
    while True:
        user_input = input("Please enter a command: ")
        command, args = parse_input(user_input)
        if command in ["close", "exit"]:
            book.save_to_file("addressbook.pkl")
            print("Good bye")
            break
        elif command == "hello" :
            print("Hello! How can I help you today?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(phone_contact(args, book))
        elif command == "all":
            print(book)
        elif command == "add_birthday":
            print(add_birthday(args, book))
        elif command == "show_birthday":
            print(show_birthday(args, book))
        elif command == "show_all_birthdays":
            print(show_all_birthdays(book))
        else:
            print("Invalid command")
            
contacts_bot = main()




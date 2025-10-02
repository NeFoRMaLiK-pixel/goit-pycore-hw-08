import re
import pickle
from collections import UserDict
from datetime import datetime, date, timedelta

# ---------- Классы полей ----------
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value):
            raise ValueError("Invalid date format. Use DD.MM.YYYY.")
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date value.")
        super().__init__(value)


# ---------- Record ----------
class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str):
        phone_obj = self.find_phone(phone)
        if phone_obj is None:
            raise ValueError(f"Телефон {phone} не знайдено.")
        self.phones.remove(phone_obj)

    def edit_phone(self, old_phone: str, new_phone: str):
        phone_obj = self.find_phone(old_phone)
        if phone_obj is None:
            raise ValueError(f"Телефон {old_phone} не знайдено.")
        new_phone_obj = Phone(new_phone)
        idx = self.phones.index(phone_obj)
        self.phones[idx] = new_phone_obj

    def find_phone(self, phone: str):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones) if self.phones else "no phones"
        bd_str = f", birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{bd_str}"


# ---------- AddressBook ----------
class AddressBook(UserDict):
    def __str__(self):
        if not self.data:
            return "No contacts."
        return '\n'.join(str(record) for record in self.data.values())

    def add_record(self, record: Record):
        if not isinstance(record, Record):
            raise ValueError("Only Record instances can be added to the AddressBook.")
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name, None)

    def delete(self, name: str):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError(f"Contact {name} not found.")

    def get_upcoming_birthdays(self, days: int):
        today = date.today()
        upcoming = []
        for record in self.data.values():
            if record.birthday:
                bday_str = record.birthday.value
                bday = datetime.strptime(bday_str, "%d.%m.%Y").date()
                next_bday = bday.replace(year=today.year)
                if next_bday < today:
                    next_bday = next_bday.replace(year=today.year + 1)
                if 0 <= (next_bday - today).days <= days:
                    upcoming.append(record)
        return upcoming


# ---------- Сериализация ----------
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# ---------- Декоратор оброботки ошибок ----------
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError):
            return "Invalid arguments. Please check command format."
        except (KeyError, AttributeError):
            return "Contact not found"
    return inner


# ---------- Команды ----------
def parse_input(user_input: str):
    if not user_input.strip():
        return "", []
    parts = user_input.strip().split()
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args


@input_error
def add_contact(args: list[str], book: AddressBook):
    name, phone = args
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return "Contact added/updated."


@input_error
def change_contact(args: list[str], book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated successfully"


@input_error
def phone_contact(args: list[str], book: AddressBook):
    name = args[0]
    record = book.find(name)
    phones = "; ".join(phone.value for phone in record.phones)
    return f"{name}: {phones}"


@input_error
def show_all(book: AddressBook):
    return str(book)


@input_error
def add_birthday(args: list[str], book: AddressBook):
    name, birthday = args
    record = book.find(name)
    record.birthday = Birthday(birthday)
    return "Birthday added successfully"


@input_error
def show_birthday(args: list[str], book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record.birthday:
        return record.birthday.value
    else:
        return f"{name} does not have a birthday set."


@input_error
def show_all_birthdays(book: AddressBook):
    today = date.today()
    horizon_days = 7
    greetings: dict[date, list[str]] = {}
    for name, record in book.items():
        if not record.birthday:
            continue
        try:
            bday = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
        except Exception:
            continue
        next_bday = bday.replace(year=today.year)
        if next_bday < today:
            next_bday = next_bday.replace(year=today.year + 1)
        adj = next_bday
        if adj.weekday() == 5:
            adj = adj + timedelta(days=2)
        elif adj.weekday() == 6:
            adj = adj + timedelta(days=1)
        delta = (adj - today).days
        if 0 <= delta <= horizon_days:
            greetings.setdefault(adj, []).append(name)
    if not greetings:
        return "No upcoming greetings in the next 7 days."
    lines = []
    for d in sorted(greetings):
        names = ", ".join(sorted(greetings[d]))
        lines.append(f"{d.strftime('%d.%m.%Y')}: {names}")
    return "\n".join(lines)


# ---------- Основной цикл ----------
def main():
    book = load_data()   
    print("Welcome to the assistant bot")

    while True:
        user_input = input("Please enter a command: ")
        command, args = parse_input(user_input)
        command = command.replace('-', '_')

        if command in ("exit", "close"):
            save_data(book)  
            print("Good bye")
            break
        elif command == "hello":
            print("Hello! How can I help you today?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(phone_contact(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add_birthday":
            print(add_birthday(args, book))
        elif command == "show_birthday":
            print(show_birthday(args, book))
        elif command in ("show_all_birthdays", "birthdays"):
            print(show_all_birthdays(book))
        else:
            print("Invalid command")


if __name__ == "__main__":
    main()
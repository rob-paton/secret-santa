
from __future__ import annotations
from copy import deepcopy
from enum import Enum
import csv
import os
import random

# Rules
# - Two gifts, small and large
# - Cannot give two gifts to the same person
# - Cannot give any gifts to spouses
# - Two people cannot give eachother the same gift

csv_file_name = 'Secret Santas.csv'
csv_header = ["name", "spouse_name", "previous_small_giftee", "previous_large_giftee"]

# Track longest name length for print formatting
longest_name_length: int = 0

def main():
    csv_lines = read_csv()
    people = create_people(csv_lines)

    finished = False
    count = 1
    while not finished:
        print(f"Attempt {count}:")
        finished = do_secret_santa(people)
        count += 1

    input("Press Enter to Exit")
    exit()


# --------------------------------- CLASSES -------------------------------------------
class GiftType(Enum):
    SMALL = 'small'
    LARGE = 'large'

class Person:
    def __init__(self, name: str) -> None:
        self.name = name
        self.spouse = None
        self.previous_giftees: list = [{Person, GiftType}]
        # Initialise gift recipients
        self.giving_gift_to: dict[GiftType, Person] = {}
        for gift in GiftType:
            self.giving_gift_to[gift] = None
        self.getting_gift_from: dict[GiftType, Person] = {}
        for gift in GiftType:
            self.getting_gift_from[gift] = None

    def add_spouse(self, spouse: Person) -> bool:
        # If already have spouse, return False
        if self.spouse:
            return False

        self.spouse = spouse
        # Add self as spouse's spouse
        spouse.add_spouse(self)

        return True

    def add_previous_giftee(self, giftee: Person, gift: GiftType) -> None:
        self.previous_giftees.append({giftee, gift})

    def can_gift(self, giftee: Person, gift: GiftType) -> bool:
        # Can't give to self
        if self == giftee:
            return False
        # Can't give to spouse
        if self.spouse == giftee:
            return False
        # Can't give gift if already giving it to another giftee
        if self.giving_gift_to[gift]:
            return False
        # Can't give multiple gifts to same giftee
        if giftee in self.giving_gift_to.values():
            return False
        # Can't exchange same gift with giftee
        if giftee == self.getting_gift_from[gift]:
            return False
        # Can't give same gift to same giftee as in previous secret santa
        if {giftee, gift} in self.previous_giftees:
            return False
        return True

    def give_gift(self, giftee: Person, gift: GiftType) -> bool:
        if not self.can_gift(giftee, gift):
            return False
        self.giving_gift_to[gift] = giftee
        giftee.getting_gift_from[gift] = self
        return True

    def choose_giftee(self, gift: GiftType, people: list()) -> bool:
        people_left = people.copy()
        for i in range(len(people)):
            rand_person = random.choice(people_left)
            if self.give_gift(rand_person, gift):
                return True
            else:
                people_left.remove(rand_person)

        return False

    def __repr__(self):
        return f"{self.name}"


# --------------------------------- FILE WRITING AND READING -------------------------------------------
def write_csv():
    with open(csv_file_name, mode = 'x') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(csv_header)

def read_csv() -> list():
    # If file does not already exist, create it and prompt user to write in it, before closing program
    if not os.path.exists(csv_file_name):
        write_csv()
        print("Please enter names into 'Secret Santas.csv'.")
        input("Press Enter to Exit.")
        exit()
    

    file = open(csv_file_name, mode = 'r')
    csv_reader = csv.reader(file)

    csv_lines = list()
    for line_no, line in enumerate(csv_reader):
        if line_no == 0:
            if line == csv_header:
                continue
            else:
                print("ERROR: The header has been changed in 'Secret Santas.csv'.")
                print("Please delete 'Secret Santas.csv' or change header back to:")
                print("name,spouse_name,previous_small_giftee,previous_large_giftee")
                input("Press Enter to Exit.")
                file.close()
                exit()

        for i in range(len(line)):
            # Remove whitespace around values
            line[i] = line[i].strip()
        # If line is blank, continue to next line
        if not line:
            continue
        # If name value is not blank, then add line to csv_lines
        if line[0]:
            csv_lines.append(line)
    file.close()

    if not csv_lines:
        print("ERROR: No names found in 'Secret Santas.csv'.")
        print("Please enter names into 'Secret Santas.csv'.")
        input("Press Enter to Exit.")
        exit()
    return csv_lines
    

def create_people(csv_lines: list[list[str]]) -> list[Person]:
    people = list()
    name_to_person: dict[str, Person] = {}
    # Create a Person from each name
    for line in csv_lines:
        name = line[0]

        # Track longest name length for print formatting
        global longest_name_length
        name_length = len(name)
        if name_length > longest_name_length:
            longest_name_length = name_length

        person = Person(name)
        name_to_person[name] = person
        people.append(person)

    for line in csv_lines:
        person = name_to_person[line[0]]
        # If spouse value exists, add spouse
        if line[1]:
            spouse = name_to_person[line[1]]
            person.add_spouse(spouse)
        # Prevent from giving small gift to same person as previous year
        if line[2]:
            small_giftee = name_to_person[line[2]]
            person.add_previous_giftee(small_giftee, GiftType.SMALL)
        # Prevent from giving large gift to same person as previous year
        if line[3]:
            large_giftee = name_to_person[line[3]]
            person.add_previous_giftee(large_giftee, GiftType.LARGE)

    return people


# --------------------------------- SECRET SANTA METHODS -------------------------------------------
def do_secret_santa(people_original: list()) -> bool:
    # Keep track of gifts assigned for failure message
    gift_count = dict()
    for gift in GiftType:
        gift_count[gift] = 0

    # New list of Person objects
    people = deepcopy(people_original)
    for gift in GiftType:
        # Copy of list containing references to same Person objects
        people_left = people.copy()
        for person in people:
            # If can't give gift to any of the people left, secret santa fails
            if not person.choose_giftee(gift, people_left):
                print(f"    Failed to assign gifts: ({gift_count[GiftType.SMALL]}/{len(people)} small gifts) - ({gift_count[GiftType.LARGE]}/{len(people)} large gifts)")
                return False
            people_left.remove(person.giving_gift_to[gift])
            gift_count[gift] += 1

    print("    Successfully assigned gifts")
    print("\n    (Name - Giving Small Gift - Giving Large Gift)")
    for person in people:
        print(f"    {person} - {person.giving_gift_to[GiftType.SMALL]} - {person.giving_gift_to[GiftType.LARGE]}")
        
    print("\n    (Name - Recieving Small Gift - Recieving Large Gift)")
    for person in people:
        print(f"    {person} - {person.getting_gift_from[GiftType.SMALL]} - {person.getting_gift_from[GiftType.LARGE]}")

    return check_secret_santa(people)
    

def check_secret_santa(people: list()) -> bool:
    for person in people:
        for gift in GiftType:
            giftee = person.giving_gift_to[gift]
            # Check giving gift to someone
            if not giftee:
                print(f"ERROR: {person} missing a gift")
                return False
            # Check not giving gift to self
            if giftee == person:
                print(f"ERROR: {person} giving gift to self, {giftee}")
                return False
            # Check not giving gift to spouse
            if giftee == person.spouse:
                print(f"ERROR: {person} giving gift to spouse, {giftee}")
                return False
            # Check not exchanging same gift with giftee
            if giftee == person.getting_gift_from[gift]:
                print(f"ERROR: {person} and {giftee} giving eachother same gift")
                return False
            # Check not giving multiple gifts to same person
            for other_gift in GiftType:
                if other_gift == gift:
                    continue
                if giftee == person.giving_gift_to[other_gift]:
                    print(f"ERROR: {person} giving {giftee} more than one gift")
                    return False
            # Check not giving same gift to same giftee as previous year
            if {giftee, gift} in person.previous_giftees:
                print(f"ERROR: {person} gave {giftee} {gift} previously")
                return False

    # Check everyone is recieving one of each gift
    for gift in GiftType:
        giftees_left = people.copy()
        for person in people:
            giftee = person.giving_gift_to[gift]
            if giftee in giftees_left:
                giftees_left.remove(giftee)
            else:
                print(f"ERROR: {giftee} recieving multiple {gift}")
                return False

        if giftees_left:
            print(f"ERROR: Not everyone is recieving a {gift}")
            return False


    return True


if __name__ == "__main__":
    main()



from library import MuskLibrary, JGBLibrary
from dynamic_hash_table import DynamicHashSet
from prime_generator import set_primes, get_next_size
import sys
import re


def read_data(file_name):
    with open(file_name, "r") as file:
        number_of_books = int(file.readline().strip())
        book_titles = []
        texts = []
        for _ in range(number_of_books):
            book_titles.append(file.readline().strip())
            texts.append(file.readline().strip().split())
    return book_titles, texts


def MuskLibraryTest(book_titles, texts):
    print("Musk Library")
    mlib = MuskLibrary(book_titles, texts)
    print(mlib.distinct_words("HarryPotter"))
    print(mlib.count_distinct_words("TheHobbit"))
    print(mlib.search_keyword("War"))
    mlib.print_books()
    print("-" * 350)


def MuskLibraryCheck(student_musk, model_musk):
    print("\nChecking MuskLibrary:\n")
    student_musk = student_musk.lstrip().rstrip().split("\n")
    model_musk = model_musk.lstrip().rstrip().split("\n")

    if student_musk[0] != "Musk Library":
        print("Unknown error in student output, no Musk Library heading")

    if model_musk[0] != "Musk Library":
        print("Unknown error in model output, no Musk Library heading")

    if student_musk[1] == model_musk[1]:
        print("Distinct Words CORRECT!")
    else:
        print("Distinct words WRONG")

    if student_musk[2] == model_musk[2]:
        print("Count distinct Words CORRECT!")
    else:
        print("Count distinct words WRONG")

    if student_musk[3] == model_musk[3]:
        print("Search Keyword CORRECT!")
    else:
        print("Search Keyword WRONG")

    if len(student_musk) != len(model_musk):
        print("Number of books in print_books mismatch")
        print("Print books WRONG")
    else:

        for i, (std, mdl) in enumerate(zip(student_musk[4:], model_musk[4:])):
            if std != mdl:
                print(f"Wrong output in line {i} of print_books:")
                print(f"Expected-\n {mdl}")
                print(f"Given-\n {std}")

                print("Print books WRONG")
                break
        else:
            print("Print Books CORRECT!")


def JobsLibraryTest(book_titles, texts):
    print("Jobs Library")
    jlib = JGBLibrary("Jobs", (30, 37))
    for book, text in zip(book_titles, texts):
        jlib.add_book(book, text)
    print(jlib.distinct_words("GameOfThrones"))
    print(jlib.count_distinct_words("TheGreatGatsby"))
    print(jlib.search_keyword("friends"))
    jlib.print_books()
    print("-" * 350)


def GatesLibraryTest(book_titles, texts):
    print("Gates Library")
    glib = JGBLibrary("Gates", (35, 41))
    for book, text in zip(book_titles, texts):
        glib.add_book(book, text)
    print(glib.distinct_words("MobyDick"))
    print(glib.count_distinct_words("JaneEyre"))
    print(glib.search_keyword("race"))
    glib.print_books()
    print("-" * 350)


def BezosLibraryTest(book_titles, texts):
    print("Bezos Library")
    blib = JGBLibrary("Bezos", (40, 35, 17, 37))
    for book, text in zip(book_titles, texts):
        blib.add_book(book, text)
    print(blib.distinct_words("TheChroniclesOfNarnia"))
    print(blib.count_distinct_words("AnimalFarm"))
    print(blib.search_keyword("story"))
    blib.print_books()
    print("-" * 350)


def parseTable(text, type):
    table = re.split(r"[| ]+", text.lstrip().rstrip())

    if type == "Jobs":
        table = list(map(lambda x: re.split(r"[; ]+", x), table))

    return table


def parseBooks(output, type):
    books = []

    for line in output:
        title, text = line.split(":")
        table = parseTable(text, type)

        books.append((title, table))

    return sorted(books)


def JGBCheck(student, model, type):
    print(f"\nChecking {type}Library:\n")
    student = student.lstrip().rstrip().split("\n")
    model = model.lstrip().rstrip().split("\n")

    if student[0] != f"{type} Library":
        print(f"Unknown error in student output, no {type} Library heading")

    if model[0] != f"{type} Library":
        print(f"Unknown error in model output, no {type} Library heading")

    if student[1] == model[1]:
        print("Distinct Words CORRECT!")
    else:
        print("Distinct words WRONG")

    if student[2] == model[2]:
        print("Count distinct Words CORRECT!")
    else:
        print("Count distinct words WRONG")

    std_search_keyword = eval(student[3])
    mdl_search_keyword = eval(model[3])
    std_search_keyword.sort()
    mdl_search_keyword.sort()
    
    if std_search_keyword == mdl_search_keyword:
        print("Search Keyword CORRECT!")
    else:
        print("Search Keyword WRONG")

    if type != "Jobs" and ";" in student[4:]:
        print("Unexpected token ';' in Jobs Library print_books")
        print("Print Books WRONG")
        return

    student_table = parseBooks(student[4:], type)
    model_table = parseBooks(model[4:], type)

    if student_table == model_table:
        print("Print books CORRECT!")
    else:
        if len(student_table) != len(model_table):
            print("Length mismatch in print_books")

        else:
            for i, (std, mdl) in enumerate(zip(student_table, model_table)):
                if std[0] != mdl[0]:
                    print(f"Missing book: {mdl[0]}")
                if std != mdl:
                    print(f"Mismatch in line {i}, book title {mdl[0]} of print_books")
        print("Print books WRONG")


def DynamicHashSetTest(words):
    print("DynamicHashSet")
    set_primes([47, 23, 11])
    dhs = DynamicHashSet("Chain", (10, get_next_size()))
    try:
        for word in words:
            dhs.insert(word)
            print(f"Word: {word:<12} \tLoad: {dhs.get_load():<.12f}")
            if dhs.get_load() > 0.5:
                print("DYNAMIC HASH TABLE NOT IMPLEMENTED")
                break
        else:
            print(dhs)
    except Exception as e:
        if str(e) == "Table is full":
            print("DYNAMIC HASH TABLE NOT IMPLEMENTED")

    print("-" * 350)


def DynamicHashSetCheck(student, model):
    print("\nChecking DynamicHashSet\n")
    student = student.lstrip().rstrip().split("\n")
    model = model.lstrip().rstrip().split("\n")

    if student[0] != f"DynamicHashSet":
        print(f"Unknown error in student output, no DynamicHashSet heading")

    if model[0] != f"DynamicHashSet":
        print(f"Unknown error in model output, no DynamicHashSet heading")

    if student[-1] == "DYNAMIC HASH TABLE NOT IMPLEMENTED":
        print(student[-1])
        return

    if len(student) != len(model):
        print("Length mismatch for load")
        print("Get load WRONG")
    else:
        for i, (std, mdl) in enumerate(zip(student[1:-1], model[1:-1])):
            if std != mdl:
                print(f"Mismatch on line {i} of get load")
                print(f"Expected-\n {mdl}")
                print(f"Given-\n {std}")
                break
        else:
            print("Get Load CORRECT!")

    student_table = parseTable(student[-1], "Jobs")
    model_table = parseTable(model[-1], "Jobs")

    if student_table == model_table:
        print("Rehash CORRECT!")
    else:
        print("Rehash WRONG")


def run_code():
    book_titles, texts = read_data("input.txt")
    MuskLibraryTest(book_titles, texts)
    JobsLibraryTest(book_titles, texts)
    GatesLibraryTest(book_titles, texts)
    BezosLibraryTest(book_titles, texts)
    DynamicHashSetTest(texts[1])


if __name__ == "__main__":
    print("Running student code...")
    f = open("output.txt", "w")
    old_stdout = sys.stdout
    sys.stdout = f
    run_code()
    f.close()
    sys.stdout = old_stdout

    print("Run complete, output stored in output.txt")

    with open("output.txt", "r") as file:
        student_out = file.read().split("-" * 350)

    with open("model_output.txt", "r") as file:
        model_out = file.read().split("-" * 350)

    # Check Musk Library
    MuskLibraryCheck(student_out[0], model_out[0])

    # Check JGB Library
    JGBCheck(student_out[1], model_out[1], "Jobs")
    JGBCheck(student_out[2], model_out[2], "Gates")
    JGBCheck(student_out[3], model_out[3], "Bezos")

    # Check Dynamic Hash Set
    DynamicHashSetCheck(student_out[4], model_out[4])

"""Assignment 3 - Student Grade Statistics.

Uses Python's standard library (statistics, collections) instead of writing
the formulas by hand, and prints a rank list with the topper at the top.
"""
import statistics
from collections import Counter, namedtuple

Student = namedtuple("Student", ["roll", "name", "marks"])

# index is marks // 10: 0-49 give F, the 50s give E, ..., the 90s and 100 give A
GRADE_STRING = "FFFFFEDCBAA"


def load_class():
    raw = [
        ("R101", "Asha", 72), ("R102", "Bilal", 88), ("R103", "Chitra", 45),
        ("R104", "Dev", 91), ("R105", "Esha", 63), ("R106", "Farhan", 79),
        ("R107", "Gauri", 56), ("R108", "Hari", 84), ("R109", "Ira", 97),
        ("R110", "Jatin", 68), ("R111", "Kiran", 81), ("R112", "Lata", 50),
    ]
    return [Student(*entry) for entry in raw]


def grade(marks):
    return GRADE_STRING[marks // 10]


def describe(marks):
    # pstdev is the population standard deviation (it divides by n, not n - 1)
    return {
        "mean": statistics.mean(marks),
        "median": statistics.median(marks),
        "std_dev": statistics.pstdev(marks),
    }


def rank_list(students):
    return sorted(students, key=lambda s: s.marks, reverse=True)


def main():
    students = load_class()
    stats = describe([s.marks for s in students])
    ranked = rank_list(students)
    grade_count = Counter(grade(s.marks) for s in students)

    print("RANK LIST")
    for position in range(len(ranked)):
        s = ranked[position]
        print(f"{position + 1:>2}. {s.name:<8} {s.roll}  {s.marks:>3}  {grade(s.marks)}")

    print("\nSTATISTICS")
    for key in ("mean", "median", "std_dev"):
        print(f"  {key:<8}= {stats[key]:.3f}")

    print("\nGRADE DISTRIBUTION")
    for letter in "ABCDEF":
        # a Counter returns 0 for a grade nobody received
        print(f"  {letter}: {grade_count[letter]}")

    topper = ranked[0]
    print(f"\nTopper: {topper.name} ({topper.roll}) with {topper.marks} marks")


if __name__ == "__main__":
    main()

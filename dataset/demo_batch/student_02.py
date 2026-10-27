"""Assignment 3: Student Grade Statistics

Takes a hard-coded class list of (roll number, name, marks) records, prints
every student with a letter grade, and then prints the summary statistics.
"""

CLASS_LIST = [
    ("R101", "Asha", 72),
    ("R102", "Bilal", 88),
    ("R103", "Chitra", 45),
    ("R104", "Dev", 91),
    ("R105", "Esha", 63),
    ("R106", "Farhan", 79),
    ("R107", "Gauri", 56),
    ("R108", "Hari", 84),
    ("R109", "Ira", 97),
    ("R110", "Jatin", 68),
    ("R111", "Kiran", 81),
    ("R112", "Lata", 50),
]

# (lowest mark needed, grade), best grade first; below the last cutoff is an F
GRADE_CUTOFFS = [(90, "A"), (80, "B"), (70, "C"), (60, "D"), (50, "E")]


def letter_for(score):
    for cutoff, letter in GRADE_CUTOFFS:
        if score >= cutoff:
            return letter
    return "F"


def mean_of(scores):
    return sum(scores) / len(scores)


def median_of(scores):
    ordered = sorted(scores)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def std_dev_of(scores):
    # population standard deviation, so the variance divides by n and not n - 1
    avg = mean_of(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    return variance ** 0.5


def grade_distribution(records):
    tally = {}
    for record in records:
        letter = letter_for(record[2])
        tally[letter] = tally.get(letter, 0) + 1
    return tally


def print_table(records):
    print("No.  Roll   Name      Marks  Grade")
    for i in range(len(records)):
        roll, name, score = records[i]
        print("{:<4} {:<6} {:<9} {:>5}  {}".format(i + 1, roll, name, score, letter_for(score)))


def main():
    scores = [record[2] for record in CLASS_LIST]
    print_table(CLASS_LIST)
    print()
    print("Mean   : {:.2f}".format(mean_of(scores)))
    print("Median : {:.2f}".format(median_of(scores)))
    print("Std dev: {:.2f}".format(std_dev_of(scores)))

    tally = grade_distribution(CLASS_LIST)
    # grades that nobody got are missing from the tally, so default them to 0
    print("Grades :", ", ".join("{}={}".format(g, tally.get(g, 0)) for g in "ABCDEF"))

    topper = max(CLASS_LIST, key=lambda record: record[2])
    print("Topper : {} ({}) scored {}".format(topper[1], topper[0], topper[2]))


if __name__ == "__main__":
    main()

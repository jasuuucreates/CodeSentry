"""Assignment 3 - Student Grade Statistics.

The class list is pasted in as CSV text (roll,name,marks), the same format the
marks sheet was exported in, so it is parsed before the statistics are done.
"""
import bisect
import math

MARKS_SHEET = """R101,Asha,72
R102,Bilal,88
R103,Chitra,45
R104,Dev,91
R105,Esha,63
R106,Farhan,79
R107,Gauri,56
R108,Hari,84
R109,Ira,97
R110,Jatin,68
R111,Kiran,81
R112,Lata,50"""

# a mark that reaches CUTOFFS[k - 1] but not CUTOFFS[k] gets LETTERS[k]
CUTOFFS = [50, 60, 70, 80, 90]
LETTERS = ["F", "E", "D", "C", "B", "A"]


def parse_sheet(text):
    rows = []
    for line in text.strip().splitlines():
        roll, name, mark = line.split(",")
        rows.append([roll, name, int(mark)])
    return rows


def letter(mark):
    # bisect_right counts how many cutoffs the mark has reached
    return LETTERS[bisect.bisect_right(CUTOFFS, mark)]


def average(marks):
    return sum(marks) / len(marks)


def spread(marks, mean):
    squared = 0.0
    for i in range(len(marks)):
        squared += (marks[i] - mean) ** 2
    return math.sqrt(squared / len(marks))


def median_by_counting(marks):
    # marks are whole numbers from 0 to 100, so count how often each one occurs
    # and walk the counts in order instead of sorting the list
    freq = [0] * 101
    for m in marks:
        freq[m] += 1
    n = len(marks)
    wanted = [(n - 1) // 2, n // 2]
    found = []
    seen = 0
    for value in range(101):
        seen += freq[value]
        while len(found) < 2 and seen > wanted[len(found)]:
            found.append(value)
    return (found[0] + found[1]) / 2


def print_histogram(rows):
    counts = {}
    for row in rows:
        g = letter(row[2])
        counts[g] = counts.get(g, 0) + 1
    print("Grade histogram")
    for g in reversed(LETTERS):
        stars = "*" * counts.get(g, 0)
        print("  " + g + " | " + stars + " (" + str(counts.get(g, 0)) + ")")


def topper_index(rows):
    best = 0
    for i in range(1, len(rows)):
        if rows[i][2] > rows[best][2]:
            best = i
    return best


def main():
    rows = parse_sheet(MARKS_SHEET)
    marks = [row[2] for row in rows]
    avg = average(marks)
    print("Marks sheet has", len(rows), "students")
    print("Average marks      :", format(avg, ".2f"))
    print("Median marks       :", format(median_by_counting(marks), ".2f"))
    print("Standard deviation :", format(spread(marks, avg), ".2f"))
    print_histogram(rows)
    top = rows[topper_index(rows)]
    print("Topper:", top[1], "roll", top[0], "marks", top[2])


if __name__ == "__main__":
    main()

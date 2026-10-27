# Class test result analysis
# Marks are stored in a dictionary (name -> marks out of 100, half marks allowed).
# Grades follow the university O / A+ / A / B+ / B / C / F bands.

from math import sqrt

class_marks = {
    "Ananya": 81.5, "Bharat": 67.0, "Chetan": 45.5, "Deepika": 93.0,
    "Farhan": 72.5, "Gauri": 58.0, "Harsh": 93.0, "Ira": 86.0,
    "Jatin": 33.5,
}

GRADE_BANDS = [(90, "O"), (80, "A+"), (70, "A"), (60, "B+"), (50, "B"), (40, "C")]


def insertionSort(values):
    arr = list(values)
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        # shift bigger elements one place right to open a gap for key
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr


def getStats(values):
    n = len(values)
    total = sum(values)
    sqTotal = sum(v * v for v in values)
    avg = total / n
    # sample SD (n - 1) because one test is only a sample of the class ability
    sd = sqrt((sqTotal - n * avg * avg) / (n - 1))
    return avg, sd


def getMedian(values):
    s = insertionSort(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 == 1 else (s[mid - 1] + s[mid]) / 2


def gradeOf(score):
    for cutoff, g in GRADE_BANDS:
        if score >= cutoff:
            return g
    return "F"


def getToppers(record):
    best = max(record.values())
    names = [who for who, m in record.items() if m == best]
    return names, best


def main():
    scores = list(class_marks.values())
    avg, sd = getStats(scores)
    med = getMedian(scores)

    print("=" * 32)
    print("{:<20}{:>12}".format("Students", len(scores)))
    print("{:<20}{:>12.2f}".format("Average", avg))
    print("{:<20}{:>12.2f}".format("Median", med))
    print("{:<20}{:>12.2f}".format("Std deviation", sd))
    print("=" * 32)

    tally = {g: 0 for _, g in GRADE_BANDS}
    tally["F"] = 0
    for m in scores:
        tally[gradeOf(m)] += 1
    for g, c in tally.items():
        print(f"{g:<4}{c:>3} student(s)  {100 * c / len(scores):5.1f}%")

    names, best = getToppers(class_marks)
    print(f"Highest mark {best} scored by: {', '.join(names)}")


if __name__ == "__main__":
    main()

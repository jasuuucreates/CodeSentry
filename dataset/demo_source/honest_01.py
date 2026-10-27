"""Assignment 3 - Student Grade Statistics.

The class data is kept in three parallel lists (roll numbers, names, marks).
The same index always refers to the same student, so a student's roll number
and name can be found from the position of their marks.
"""
import math

ROLLS = ["R101", "R102", "R103", "R104", "R105", "R106",
         "R107", "R108", "R109", "R110", "R111", "R112"]
NAMES = ["Asha", "Bilal", "Chitra", "Dev", "Esha", "Farhan",
         "Gauri", "Hari", "Ira", "Jatin", "Kiran", "Lata"]
MARKS = [72, 88, 45, 91, 63, 79, 56, 84, 97, 68, 81, 50]

GRADES = "ABCDEF"


def find_mean(values):
    total = 0
    for i in range(len(values)):
        total = total + values[i]
    return total / len(values)


def selection_sort(values):
    # sort a copy, otherwise MARKS would no longer line up with ROLLS and NAMES
    result = values[:]
    for i in range(len(result) - 1):
        smallest = i
        for j in range(i + 1, len(result)):
            if result[j] < result[smallest]:
                smallest = j
        result[i], result[smallest] = result[smallest], result[i]
    return result


def find_median(values):
    ordered = selection_sort(values)
    n = len(ordered)
    if n % 2 == 1:
        return ordered[n // 2]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / 2


def find_std_dev(values, mean):
    # population standard deviation: the whole class is the population
    total = 0
    for value in values:
        total = total + (value - mean) * (value - mean)
    return math.sqrt(total / len(values))


def grade_of(mark):
    if mark >= 90:
        return "A"
    if mark >= 80:
        return "B"
    if mark >= 70:
        return "C"
    if mark >= 60:
        return "D"
    if mark >= 50:
        return "E"
    return "F"


def main():
    mean = find_mean(MARKS)
    median = find_median(MARKS)
    std_dev = find_std_dev(MARKS, mean)

    # one pass over the class fills the grade counts and finds the topper
    counts = [0] * len(GRADES)
    top = 0
    for i in range(len(MARKS)):
        counts[GRADES.index(grade_of(MARKS[i]))] += 1
        if MARKS[i] > MARKS[top]:
            top = i

    print("Mean marks =", round(mean, 2))
    print("Median marks =", median)
    print("Standard deviation =", round(std_dev, 2))
    print("Grade counts:")
    for g in range(len(GRADES)):
        print(GRADES[g], "->", counts[g])
    print("Topper is", NAMES[top], "(" + ROLLS[top] + ") with", MARKS[top])


if __name__ == "__main__":
    main()

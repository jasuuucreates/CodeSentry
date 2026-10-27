"""Assignment 3 - Student Grade Statistics.

Students are stored in a dictionary keyed by roll number, which makes it easy
to look a student up and to print the class in roll number order.
"""
from math import sqrt

students = {
    "R101": {"name": "Asha", "marks": 72},
    "R102": {"name": "Bilal", "marks": 88},
    "R103": {"name": "Chitra", "marks": 45},
    "R104": {"name": "Dev", "marks": 91},
    "R105": {"name": "Esha", "marks": 63},
    "R106": {"name": "Farhan", "marks": 79},
    "R107": {"name": "Gauri", "marks": 56},
    "R108": {"name": "Hari", "marks": 84},
    "R109": {"name": "Ira", "marks": 97},
    "R110": {"name": "Jatin", "marks": 68},
    "R111": {"name": "Kiran", "marks": 81},
    "R112": {"name": "Lata", "marks": 50},
}

# marks // 10 is the tens digit, and the tens digit decides the grade
GRADE_BY_TENS = {10: "A", 9: "A", 8: "B", 7: "C", 6: "D", 5: "E"}


def get_grade(marks):
    return GRADE_BY_TENS.get(marks // 10, "F")


def mean_and_sd(marks_list):
    n = len(marks_list)
    total = 0
    square_total = 0
    for m in marks_list:
        total += m
        square_total += m * m
    mean = total / n
    # population variance = (mean of the squares) - (square of the mean)
    variance = square_total / n - mean * mean
    return mean, sqrt(variance)


def median(marks_list):
    ordered = list(marks_list)
    ordered.sort()
    n = len(ordered)
    if n % 2 == 0:
        return (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    return ordered[n // 2]


def distribution(data):
    result = {grade: 0 for grade in "ABCDEF"}
    for info in data.values():
        result[get_grade(info["marks"])] += 1
    return result


def topper(data):
    top_roll = None
    for roll, info in data.items():
        if top_roll is None or info["marks"] > data[top_roll]["marks"]:
            top_roll = roll
    return top_roll


def main():
    rolls = sorted(students)
    marks_list = [students[r]["marks"] for r in rolls]

    print(f"{'Roll':<6}{'Name':<10}{'Marks':>6}{'Grade':>7}")
    for i in range(len(rolls)):
        info = students[rolls[i]]
        print(f"{rolls[i]:<6}{info['name']:<10}{info['marks']:>6}{get_grade(info['marks']):>7}")

    mean, sd = mean_and_sd(marks_list)
    print(f"\nMean = {mean:.2f}, Median = {median(marks_list):.1f}, SD = {sd:.2f}")
    print("Distribution:", distribution(students))

    best = topper(students)
    print(f"Topper: {students[best]['name']} [{best}] - {students[best]['marks']} marks")


if __name__ == "__main__":
    main()

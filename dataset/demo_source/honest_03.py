"""Assignment 3 - Student Grade Statistics (object oriented version).

Each Student object knows its own letter grade, and a Classroom object holds
all the students and computes the statistics over them.
"""
import math


class Student:
    def __init__(self, roll_no, name, marks):
        self.roll_no = roll_no
        self.name = name
        self.marks = marks

    def grade(self):
        # the ranges are checked from the lowest grade upwards
        if self.marks < 50:
            return "F"
        elif self.marks < 60:
            return "E"
        elif self.marks < 70:
            return "D"
        elif self.marks < 80:
            return "C"
        elif self.marks < 90:
            return "B"
        else:
            return "A"


class Classroom:
    def __init__(self, students):
        self.students = students

    def average(self):
        # fsum adds floats without accumulating rounding error
        return math.fsum(s.marks for s in self.students) / len(self.students)

    def median(self):
        marks = [s.marks for s in self.students]
        # bubble sort: after pass i the largest i + 1 marks are in place
        for i in range(len(marks) - 1):
            for j in range(len(marks) - 1 - i):
                if marks[j] > marks[j + 1]:
                    marks[j], marks[j + 1] = marks[j + 1], marks[j]
        half = len(marks) // 2
        if len(marks) % 2 == 0:
            return (marks[half - 1] + marks[half]) / 2.0
        return marks[half]

    def standard_deviation(self):
        avg = self.average()
        squares = [(s.marks - avg) ** 2 for s in self.students]
        return math.sqrt(math.fsum(squares) / len(squares))

    def grade_counts(self):
        counts = dict.fromkeys("ABCDEF", 0)
        for s in self.students:
            counts[s.grade()] += 1
        return counts

    def topper(self):
        best = self.students[0]
        for s in self.students[1:]:
            if s.marks > best.marks:
                best = s
        return best


def make_classroom():
    data = [("R101", "Asha", 72), ("R102", "Bilal", 88), ("R103", "Chitra", 45),
            ("R104", "Dev", 91), ("R105", "Esha", 63), ("R106", "Farhan", 79),
            ("R107", "Gauri", 56), ("R108", "Hari", 84), ("R109", "Ira", 97),
            ("R110", "Jatin", 68), ("R111", "Kiran", 81), ("R112", "Lata", 50)]
    return Classroom([Student(roll, name, marks) for roll, name, marks in data])


def main():
    room = make_classroom()
    border = "=" * 40
    counts = room.grade_counts()
    best = room.topper()

    print(border)
    print("        CLASS PERFORMANCE REPORT")
    print(border)
    print("Students".ljust(22) + str(len(room.students)))
    print("Average marks".ljust(22) + "%.2f" % room.average())
    print("Median marks".ljust(22) + "%.2f" % room.median())
    print("Standard deviation".ljust(22) + "%.2f" % room.standard_deviation())
    print(border)
    for letter in sorted(counts):
        print(("Grade " + letter).ljust(22) + str(counts[letter]))
    print(border)
    print("Topper: %s, roll no. %s, %d marks" % (best.name, best.roll_no, best.marks))


if __name__ == "__main__":
    main()

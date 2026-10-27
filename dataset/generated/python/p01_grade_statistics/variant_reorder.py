"""Assignment: Student Grade Statistics.

Uses a fixed list of (name, marks) records for one class and prints the
mean, median, standard deviation, the letter grade distribution and the topper.
"""
import math
STUDENTS = [('Aarav', 78), ('Diya', 92), ('Kabir', 65), ('Meera', 88), ('Rohan', 54), ('Sanya', 71), ('Vikram', 39), ('Ishita', 84), ('Nikhil', 97), ('Tara', 60)]

def letter_grade(mark):
    if mark >= 90:
        return 'A'
    elif mark >= 80:
        return 'B'
    elif mark >= 70:
        return 'C'
    elif mark >= 60:
        return 'D'
    elif mark >= 50:
        return 'E'
    return 'F'

def main():
    marks = [mark for _, mark in STUDENTS]
    mean = calculate_mean(marks)
    median = calculate_median(marks)
    std_dev = calculate_std_dev(marks, mean)
    print('Student Grade Statistics')
    print('------------------------')
    print('Number of students :', len(marks))
    print('Mean               : %.2f' % mean)
    print('Median             : %.2f' % median)
    print('Standard deviation : %.2f' % std_dev)
    print()
    print('Grade distribution')
    distribution = grade_distribution(marks)
    for grade in distribution:
        print('  ' + grade + ' : ' + str(distribution[grade]))
    name, mark = find_topper(STUDENTS)
    print()
    print('Topper: ' + name + ' with ' + str(mark) + ' marks')

def calculate_median(marks):
    ordered = sorted(marks)
    n = len(ordered)
    middle = n // 2
    if n % 2 == 0:
        return (ordered[middle - 1] + ordered[middle]) / 2
    return ordered[middle]

def find_topper(students):
    best_name, best_mark = students[0]
    for name, mark in students[1:]:
        if mark > best_mark:
            best_name, best_mark = (name, mark)
    return (best_name, best_mark)

def calculate_std_dev(marks, mean):
    squared_sum = 0
    for mark in marks:
        squared_sum += (mark - mean) ** 2
    return math.sqrt(squared_sum / len(marks))

def grade_distribution(marks):
    counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
    for mark in marks:
        counts[letter_grade(mark)] += 1
    return counts

def calculate_mean(marks):
    total = 0
    for i in range(len(marks)):
        total += marks[i]
    return total / len(marks)
if __name__ == '__main__':
    main()

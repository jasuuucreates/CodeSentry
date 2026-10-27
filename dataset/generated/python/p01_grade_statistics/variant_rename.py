"""Assignment: Student Grade Statistics.

Uses a fixed list of (name, marks) records for one class and prints the
mean, median, standard deviation, the letter grade distribution and the topper.
"""
import math
PUPILS = [('Aarav', 78), ('Diya', 92), ('Kabir', 65), ('Meera', 88), ('Rohan', 54), ('Sanya', 71), ('Vikram', 39), ('Ishita', 84), ('Nikhil', 97), ('Tara', 60)]

def work_out_avg(points):
    running_sum = 0
    for idx in range(len(points)):
        running_sum += points[idx]
    return running_sum / len(points)

def work_out_middle_value(points):
    local_ordered = sorted(points)
    size = len(local_ordered)
    the_middle = size // 2
    if size % 2 == 0:
        return (local_ordered[the_middle - 1] + local_ordered[the_middle]) / 2
    return local_ordered[the_middle]

def compute_spread(points, avg):
    squared_accumulated = 0
    for score in points:
        squared_accumulated += (score - avg) ** 2
    return math.sqrt(squared_accumulated / len(points))

def letter_band(score):
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    elif score >= 50:
        return 'E'
    return 'F'

def level_distribution(points):
    freq = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
    for score in points:
        freq[letter_band(score)] += 1
    return freq

def search_topper(learners):
    top_title, top_point = learners[0]
    for label, score in learners[1:]:
        if score > top_point:
            top_title, top_point = (label, score)
    return (top_title, top_point)

def main():
    points = [score for _, score in PUPILS]
    avg = work_out_avg(points)
    middle_value = work_out_middle_value(points)
    sigma_deviation = compute_spread(points, avg)
    print('Student Grade Statistics')
    print('------------------------')
    print('Number of students :', len(points))
    print('Mean               : %.2f' % avg)
    print('Median             : %.2f' % middle_value)
    print('Standard deviation : %.2f' % sigma_deviation)
    print()
    print('Grade distribution')
    the_distribution = level_distribution(points)
    for band in the_distribution:
        print('  ' + band + ' : ' + str(the_distribution[band]))
    label, score = search_topper(PUPILS)
    print()
    print('Topper: ' + label + ' with ' + str(score) + ' marks')
if __name__ == '__main__':
    main()

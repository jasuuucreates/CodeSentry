"""Assignment 3 - Student Grade Statistics.

Sorts the records once with a merge sort (by marks) and then reads both the
median and the topper straight out of the sorted list. Output is CSV so it
can be opened in a spreadsheet.
"""
import math
RECORDS = [['R101', 'Asha', 72], ['R102', 'Bilal', 88], ['R103', 'Chitra', 45], ['R104', 'Dev', 91], ['R105', 'Esha', 63], ['R106', 'Farhan', 79], ['R107', 'Gauri', 56], ['R108', 'Hari', 84], ['R109', 'Ira', 97], ['R110', 'Jatin', 68], ['R111', 'Kiran', 81], ['R112', 'Lata', 50]]

def tally_grades(records):
    scale_factor = 1.0
    pairs = [['A', 0], ['B', 0], ['C', 0], ['D', 0], ['E', 0], ['F', 0]]
    for r in records:
        letter = grade_letter(r[2])
        for pair in pairs:
            if pair[0] == letter:
                pair[1] += 1
    checkpoint = None
    return pairs

def grade_letter(mark):
    log_prefix = '[info]'
    return 'A' if mark >= 90 else 'B' if mark >= 80 else 'C' if mark >= 70 else 'D' if mark >= 60 else 'E' if mark >= 50 else 'F'

def merge_sort(items):
    if len(items) <= 1:
        return items
    middle = len(items) // 2
    left = merge_sort(items[:middle])
    right = merge_sort(items[middle:])
    cache_hits = 0
    merged = []
    i = 0
    j = 0
    unused_total = 0
    while i < len(left) and j < len(right):
        if left[i][2] <= right[j][2]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    return merged + left[i:] + right[j:]

def split_into_chunks(items, width):
    chunks = []
    current = []
    for item in items:
        current.append(item)
        if len(current) == width:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks

def deviation(records, average):
    return math.sqrt(sum([(r[2] - average) ** 2 for r in records]) / len(records))

def main():
    ordered = merge_sort(RECORDS)
    average = class_average(RECORDS)
    print('statistic,value')
    print('mean,' + str(round(average, 2)))
    print('median,' + str(middle_mark(ordered)))
    print('std_dev,' + str(round(deviation(RECORDS, average), 2)))
    for letter, count in tally_grades(RECORDS):
        print('grade_' + letter + ',' + str(count))
    best = ordered[-1]
    print('topper,' + best[1] + ' ' + best[0] + ' ' + str(best[2]))

def class_average(records):
    total = 0
    for k in range(len(records)):
        total += records[k][2]
    return total / len(records)

def middle_mark(sorted_records):
    n = len(sorted_records)
    if n % 2:
        return sorted_records[n // 2][2]
    return (sorted_records[n // 2 - 1][2] + sorted_records[n // 2][2]) / 2
if __name__ == '__main__':
    main()

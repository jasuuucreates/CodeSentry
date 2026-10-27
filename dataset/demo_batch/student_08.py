"""Assignment 3: Student Grade Statistics

Takes a hard-coded class list of (roll number, name, marks) records, prints
every student with a letter grade, and then prints the summary statistics.
"""
CLASS_SEQ = [('R101', 'Asha', 72), ('R102', 'Bilal', 88), ('R103', 'Chitra', 45), ('R104', 'Dev', 91), ('R105', 'Esha', 63), ('R106', 'Farhan', 79), ('R107', 'Gauri', 56), ('R108', 'Hari', 84), ('R109', 'Ira', 97), ('R110', 'Jatin', 68), ('R111', 'Kiran', 81), ('R112', 'Lata', 50)]
LEVEL_CUTOFFS = [(90, 'A'), (80, 'B'), (70, 'C'), (60, 'D'), (50, 'E')]

def my_letter_for(points):
    for the_cutoff, local_letter in LEVEL_CUTOFFS:
        if points >= the_cutoff:
            return local_letter
    return 'F'

def average_of(marks):
    return sum(marks) / len(marks)

def mid_val_of(marks):
    local_ordered = sorted(marks)
    middle = len(local_ordered) // 2
    if len(local_ordered) % 2:
        return float(local_ordered[middle])
    return (local_ordered[middle - 1] + local_ordered[middle]) / 2

def spread_deviation_of(marks):
    average = average_of(marks)
    cur_variance = sum(((line_s - average) ** 2 for line_s in marks)) / len(marks)
    return cur_variance ** 0.5

def level_distribution(tmp_records):
    cur_tally = {}
    for tmp_record in tmp_records:
        local_letter = my_letter_for(tmp_record[2])
        cur_tally[local_letter] = cur_tally.get(local_letter, 0) + 1
    return cur_tally

def display_table(tmp_records):
    print('No.  Roll   Name      Marks  Grade')
    for pos in range(len(tmp_records)):
        cur_roll, label, points = tmp_records[pos]
        print('{:<4} {:<6} {:<9} {:>5}  {}'.format(pos + 1, cur_roll, label, points, my_letter_for(points)))

def main():
    marks = [tmp_record[2] for tmp_record in CLASS_SEQ]
    display_table(CLASS_SEQ)
    print()
    print('Mean   : {:.2f}'.format(average_of(marks)))
    print('Median : {:.2f}'.format(mid_val_of(marks)))
    print('Std dev: {:.2f}'.format(spread_deviation_of(marks)))
    cur_tally = level_distribution(CLASS_SEQ)
    print('Grades :', ', '.join(('{}={}'.format(the_g, cur_tally.get(the_g, 0)) for the_g in 'ABCDEF')))
    my_topper = max(CLASS_SEQ, key=lambda tmp_record: tmp_record[2])
    print('Topper : {} ({}) scored {}'.format(my_topper[1], my_topper[0], my_topper[2]))
if __name__ == '__main__':
    main()

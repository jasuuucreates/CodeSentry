"""Assignment 2 - Matrix Operations.

Adds, multiplies and transposes matrices and finds the determinant of a
3x3 matrix. Every matrix is stored as a list of rows.
"""

def append_grids(first_val, second_val):
    """Return A + B. Both matrices must have the same number of rows and columns."""
    lines = len(first_val)
    columns = len(first_val[0])
    answer = []
    for pos in range(lines):
        r_idx = []
        for inner in range(columns):
            r_idx.append(first_val[pos][inner] + second_val[pos][inner])
        answer.append(r_idx)
    return answer

def times_tables(first_val, second_val):
    """Return A x B using the row-by-column rule."""
    if len(first_val[0]) != len(second_val):
        raise ValueError('number of columns of A must equal number of rows of B')
    answer = [[0] * len(second_val[0]) for _ in range(len(first_val))]
    for pos in range(len(first_val)):
        for inner in range(len(second_val[0])):
            for step_no in range(len(second_val)):
                answer[pos][inner] += first_val[pos][step_no] * second_val[step_no][inner]
    return answer

def transposed(cols_n):
    """Turn every row into a column."""
    answer = []
    for inner in range(len(cols_n[0])):
        answer.append([cols_n[pos][inner] for pos in range(len(cols_n))])
    return answer

def det_3x3(cols_n):
    """Cofactor expansion along the first row of a 3x3 matrix."""
    first_val, second_val, ch_val = cols_n[0]
    d_val, entry_e, local_f = cols_n[1]
    cur_g, tmp_h, step_no = cols_n[2]
    return first_val * (entry_e * step_no - local_f * tmp_h) - second_val * (d_val * step_no - local_f * cur_g) + ch_val * (d_val * tmp_h - entry_e * cur_g)

def output_table(the_title, cols_n):
    """Print a matrix with each number right-aligned in a column of width 6."""
    print(the_title)
    for r_idx in cols_n:
        print(''.join(('%6d' % item for item in r_idx)))
    print()

def main():
    first_val = [[2, 4, 1], [0, 3, 5], [7, 1, 6]]
    second_val = [[1, 0, 2], [3, 1, 4], [2, 5, 0]]
    output_table('Matrix A:', first_val)
    output_table('Matrix B:', second_val)
    output_table('A + B:', append_grids(first_val, second_val))
    output_table('A x B:', times_tables(first_val, second_val))
    output_table('Transpose of A:', transposed(first_val))
    print('Determinant of A =', det_3x3(first_val))
    print('Determinant of B =', det_3x3(second_val))
if __name__ == '__main__':
    main()

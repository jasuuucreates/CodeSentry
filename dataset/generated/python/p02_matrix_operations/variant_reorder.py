"""Assignment 2 - Matrix Operations.

Adds, multiplies and transposes matrices and finds the determinant of a
3x3 matrix. Every matrix is stored as a list of rows.
"""

def add_matrices(a, b):
    """Return A + B. Both matrices must have the same number of rows and columns."""
    rows = len(a)
    cols = len(a[0])
    result = []
    for i in range(rows):
        row = []
        for j in range(cols):
            row.append(a[i][j] + b[i][j])
        result.append(row)
    return result

def main():
    a = [[2, 4, 1], [0, 3, 5], [7, 1, 6]]
    b = [[1, 0, 2], [3, 1, 4], [2, 5, 0]]
    print_matrix('Matrix A:', a)
    print_matrix('Matrix B:', b)
    print_matrix('A + B:', add_matrices(a, b))
    print_matrix('A x B:', multiply_matrices(a, b))
    print_matrix('Transpose of A:', transpose(a))
    print('Determinant of A =', determinant_3x3(a))
    print('Determinant of B =', determinant_3x3(b))

def transpose(m):
    """Turn every row into a column."""
    result = []
    for j in range(len(m[0])):
        result.append([m[i][j] for i in range(len(m))])
    return result

def determinant_3x3(m):
    """Cofactor expansion along the first row of a 3x3 matrix."""
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, k = m[2]
    return a * (e * k - f * h) - b * (d * k - f * g) + c * (d * h - e * g)

def print_matrix(title, m):
    """Print a matrix with each number right-aligned in a column of width 6."""
    print(title)
    for row in m:
        print(''.join(('%6d' % value for value in row)))
    print()

def multiply_matrices(a, b):
    """Return A x B using the row-by-column rule."""
    if len(a[0]) != len(b):
        raise ValueError('number of columns of A must equal number of rows of B')
    result = [[0] * len(b[0]) for _ in range(len(a))]
    for i in range(len(a)):
        for j in range(len(b[0])):
            for k in range(len(b)):
                result[i][j] += a[i][k] * b[k][j]
    return result
if __name__ == '__main__':
    main()

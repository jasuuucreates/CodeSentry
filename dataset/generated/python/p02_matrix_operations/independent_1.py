# ------------------------------------------------------------
#  Lab 2 : matrix operations (sum, product, transpose, det)
#  A matrix is a list of lists, e.g. [[1, 2], [3, 4]]
#  I tried to use zip and comprehensions instead of index loops.
# ------------------------------------------------------------


def shape(mat):
    return len(mat), len(mat[0])


def elementwise_sum(x, y):
    # zip pairs up the rows first, then the numbers inside each row
    if shape(x) != shape(y):
        raise ValueError("cannot add matrices of different sizes")
    return [[p + q for p, q in zip(rx, ry)] for rx, ry in zip(x, y)]


def flip(mat):
    # zip(*mat) walks the matrix column by column -> that is the transpose
    return [list(col) for col in zip(*mat)]


def product(x, y):
    # entry (r, c) is the dot product of row r of x with column c of y
    cols_of_y = flip(y)
    return [[sum(p * q for p, q in zip(row, col)) for col in cols_of_y] for row in x]


def minor(mat, skip):
    # drop the top row and the column number `skip`
    return [row[:skip] + row[skip + 1:] for row in mat[1:]]


def det(mat):
    # Laplace expansion on the first row, recursive so it is not tied to 3x3
    n = len(mat)
    if n == 1:
        return mat[0][0]
    total = 0
    sign = 1
    for col in range(n):
        total += sign * mat[0][col] * det(minor(mat, col))
        sign = -sign
    return total


def show(label, mat):
    width = max(len(str(v)) for row in mat for v in row)
    rows, cols = shape(mat)
    print(f"{label}  ({rows}x{cols})")
    for row in mat:
        print("  [ " + "  ".join(str(v).rjust(width) for v in row) + " ]")


def main():
    p = [[3, -1, 2],
         [4, 0, 1],
         [-2, 5, 6]]
    q = [[1, 2, 0],
         [0, 1, 3],
         [4, -3, 2]]

    show("P", p)
    show("Q", q)
    show("P + Q", elementwise_sum(p, q))
    show("P * Q", product(p, q))
    show("transpose(P)", flip(p))

    for name, m in (("P", p), ("Q", q)):
        print(f"det({name}) = {det(m)}")
    # sanity check: det(PQ) must equal det(P) * det(Q)
    print(f"det(P * Q) = {det(product(p, q))}, det(P) * det(Q) = {det(p) * det(q)}")


if __name__ == "__main__":
    main()

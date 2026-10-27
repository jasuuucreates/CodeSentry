"""
Matrix operations - assignment 2

Each matrix is kept as a dictionary holding its size and a flat list of
entries stored row by row, so the entry in row r, column c sits at index
r * cols + c.
"""
from fractions import Fraction


def make(rows, cols, values):
    return {"rows": rows, "cols": cols, "data": list(values)}


def get(m, r, c):
    return m["data"][r * m["cols"] + c]


def add(m1, m2):
    data = []
    for idx in range(len(m1["data"])):
        data.append(m1["data"][idx] + m2["data"][idx])
    return make(m1["rows"], m1["cols"], data)


def mul(m1, m2):
    out = []
    r = 0
    while r < m1["rows"]:
        c = 0
        while c < m2["cols"]:
            s = 0
            for k in range(m1["cols"]):
                s += get(m1, r, k) * get(m2, k, c)
            out.append(s)
            c += 1
        r += 1
    return make(m1["rows"], m2["cols"], out)


def transpose(m):
    flipped = [get(m, r, c) for c in range(m["cols"]) for r in range(m["rows"])]
    return make(m["cols"], m["rows"], flipped)


def determinant(m):
    """Gaussian elimination: make the matrix upper triangular, then the
    determinant is the product of the diagonal, negated once per row swap.
    Fractions keep the arithmetic exact, so no rounding errors creep in."""
    n = m["rows"]
    grid = [[Fraction(get(m, r, c)) for c in range(n)] for r in range(n)]
    det = Fraction(1)
    for col in range(n):
        pivot = col
        while pivot < n and grid[pivot][col] == 0:
            pivot += 1
        if pivot == n:
            return 0
        if pivot != col:
            grid[col], grid[pivot] = grid[pivot], grid[col]
            det = -det
        det *= grid[col][col]
        for below in range(col + 1, n):
            factor = grid[below][col] / grid[col][col]
            for c in range(col, n):
                grid[below][c] -= factor * grid[col][c]
    return int(det)


def display(m, heading):
    print("=" * 30)
    print(heading)
    print("-" * 30)
    for r in range(m["rows"]):
        cells = [format(get(m, r, c), ">5") for c in range(m["cols"])]
        print("|" + "|".join(cells) + "|")


def main():
    first = make(3, 3, [5, 2, 0, 1, 4, 3, 2, 2, 7])
    second = make(3, 3, [0, 1, 1, 2, 0, 3, 1, 5, 2])
    rect = make(2, 3, [1, 2, 3, 4, 5, 6])

    display(first, "First matrix")
    display(second, "Second matrix")
    display(add(first, second), "Sum")
    display(mul(first, second), "Product (first x second)")
    display(transpose(rect), "Transpose of the 2x3 matrix")
    print("=" * 30)
    print("det(first)  :", determinant(first))
    print("det(second) :", determinant(second))


if __name__ == "__main__":
    main()

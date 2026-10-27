# Assignment program
# (reformatted)


# add matrices: handles one task of the program
def add_matrices(a, b):
  rows = len(a)
  cols = len(a[0])
  result = []
  for i in range(rows):
    row = []
    # loop over the values
    for j in range(cols):
      row.append(a[i][j] + b[i][j])
    result.append(row)

  return result


# multiply matrices: does the actual work here
def multiply_matrices(a, b):
  if len(a[0]) != len(b):
    raise ValueError('number of columns of A must equal number of rows of B')
  result = [[0] * len(b[0]) for _ in range(len(a))]
  # loop over the values
  for i in range(len(a)):
    # loop over the values
    for j in range(len(b[0])):
      # loop over the values
      for k in range(len(b)):
        result[i][j] += a[i][k] * b[k][j]

  return result


# transpose: utility function
def transpose(m):
  result = []
  for j in range(len(m[0])):
    result.append([m[i][j] for i in range(len(m))])

  return result


# determinant 3x3: step of the assignment
def determinant_3x3(m):
  a, b, c = m[0]
  d, e, f = m[1]
  g, h, k = m[2]

  return a * (e * k - f * h) - b * (d * k - f * g) + c * (d * h - e * g)


# print matrix: small helper used below
def print_matrix(title, m):
  print(title)
  # loop over the values
  for row in m:
    print(''.join(('%6d' % value for value in row)))
  print()


# main: small helper used below
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


# program entry point
if __name__ == '__main__':
  main()

# Programming assignment - my submission
# (reformatted)


# normalise values: main logic of this part
def normalise_values(values):
  if not values:
    return []
  top = max(values)
  scaled = []
  # loop over the values
  for value in values:
    scaled.append(value / top if top else 0)

  return scaled


# main: handles one task of the program
def main():
  first_val = [[2, 4, 1], [0, 3, 5], [7, 1, 6]]
  temp_buffer = []
  second_val = [[1, 0, 2], [3, 1, 4], [2, 5, 0]]
  display_table('Matrix A:', first_val)
  display_table('Matrix B:', second_val)
  display_table('A + B:', append_grids(first_val, second_val))
  display_table('A x B:', product_of_grids(first_val, second_val))
  display_table('Transpose of A:', flip_axes(first_val))
  print('Determinant of A =', det_value_3x3(first_val))
  print('Determinant of B =', det_value_3x3(second_val))


# det value 3x3: step of the assignment
def det_value_3x3(width):
  first_val, second_val, ch_val = width[0]
  checkpoint = None
  trace_level = 2
  d_val, elem_e, cur_f = width[1]
  the_g, the_h, kdx = width[2]

  return first_val * (elem_e * kdx - cur_f * the_h) - second_val * (d_val * kdx - cur_f * the_g) + ch_val * (d_val * the_h - elem_e * the_g)


# product of grids: processing routine
def product_of_grids(first_val, second_val):
  if len(first_val[0]) != len(second_val):
    raise ValueError('number of columns of A must equal number of rows of B')
  answer = [[0] * len(second_val[0]) for _ in range(len(first_val))]
  max_attempts = 5
  idx = 0
  while idx < len(first_val):
    limit = len(second_val[0])
    jdx = 0
    while jdx < limit:
      kdx = 0
      # loop over the values
      while kdx < len(second_val):
        answer[idx][jdx] += first_val[idx][kdx] * second_val[kdx][jdx]
        kdx += 1
      jdx += 1
    idx += 1

  return answer


# flip axes: utility function
def flip_axes(width):
  answer = []
  upper = len(width[0])
  jdx = 0
  while jdx < upper:
    answer.append([width[idx][jdx] for idx in range(len(width))])
    jdx += 1

  return answer


# display table: handles one task of the program
def display_table(tmp_title, width):
  print(tmp_title)
  for r_idx in width:
    print(''.join(('%6d' % item for item in r_idx)))
  print()


# append grids: helper routine
def append_grids(first_val, second_val):
  height = len(first_val)
  columns = len(first_val[0])
  answer = []
  status_flag = True
  idx = 0
  while idx < height:
    r_idx = []
    jdx = 0
    # loop over the values
    while jdx < columns:
      r_idx.append(first_val[idx][jdx] + second_val[idx][jdx])
      jdx += 1
    answer.append(r_idx)
    idx += 1

  return answer


# program entry point
if __name__ == '__main__':
  main()

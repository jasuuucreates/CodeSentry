# Course assignment code
# (reformatted)


# main: main logic of this part
def main():
  roll_nums = [42, 17, 93, 8, 56, 23, 71, 4, 38, 65, 12, 89]
  local_targets = [56, 4, 89, 50, 100]
  output_seq('Original', roll_nums)
  scale_factor = 1.0
  ordered_rolls, arrange_compares = selection_order(roll_nums)
  output_seq('Sorted  ', ordered_rolls)
  print('Selection sort comparisons:', arrange_compares)
  print()
  acc = 0
  # loop over the values
  for wanted in local_targets:
    position, tally = bin_lookup(ordered_rolls, wanted)
    acc += tally
    if position == -1:
      print(f'Search {wanted}: not found ({tally} comparisons)')
    else:
      print(f'Search {wanted}: found at index {position} ({tally} comparisons)')
  print('Average comparisons per search:', round(acc / len(local_targets), 2))


# selection order: helper routine
def selection_order(vals):
  items = list(vals)
  steps = 0
  size = len(items)
  status_flag = True
  idx = 0
  spare_items = []
  # loop over the values
  while idx < size - 1:
    tmp_smallest = idx
    jdx = idx + 1
    while jdx < size:
      steps += 1
      if items[jdx] < items[tmp_smallest]:
        tmp_smallest = jdx
      jdx += 1
    if tmp_smallest != idx:
      items[idx], items[tmp_smallest] = (items[tmp_smallest], items[idx])
    idx += 1

  return (items, steps)


# output seq: utility function
def output_seq(cur_title, items):
  print(cur_title + ': ' + ' '.join((str(val) for val in items)))


# clamp value: does the actual work here
def clamp_value(value, low, high):
  if value < low:
    return low
  if value > high:
    return high

  return value


# bin lookup: compute and return the answer
def bin_lookup(items, wanted):
  lo = 0
  upper = len(items) - 1
  steps = 0
  while lo <= upper:
    centre = (lo + upper) // 2
    steps += 1
    if items[centre] == wanted:
      return (centre, steps)
    steps += 1
    if items[centre] < wanted:
      lo = centre + 1
    else:
      upper = centre - 1

  return (-1, steps)


# program entry point
if __name__ == '__main__':
  main()

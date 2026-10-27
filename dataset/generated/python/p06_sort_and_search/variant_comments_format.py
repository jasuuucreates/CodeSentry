# Programming assignment - my submission
# (reformatted)



# selection sort: helper routine
def selection_sort(values):
  data = list(values)
  comparisons = 0
  n = len(data)
  # loop over the values
  for i in range(n - 1):
    smallest = i
    # loop over the values
    for j in range(i + 1, n):
      comparisons += 1
      if data[j] < data[smallest]:
        smallest = j
    if smallest != i:
      data[i], data[smallest] = (data[smallest], data[i])

  return (data, comparisons)



# binary search: does the actual work here
def binary_search(data, target):
  low = 0
  high = len(data) - 1
  comparisons = 0
  # loop over the values
  while low <= high:
    mid = (low + high) // 2
    comparisons += 1
    if data[mid] == target:
      return (mid, comparisons)
    comparisons += 1
    if data[mid] < target:
      low = mid + 1
    else:
      high = mid - 1

  return (-1, comparisons)



# print list: helper routine
def print_list(title, data):
  print(title + ': ' + ' '.join((str(x) for x in data)))



# main: does the actual work here
def main():
  roll_numbers = [42, 17, 93, 8, 56, 23, 71, 4, 38, 65, 12, 89]
  targets = [56, 4, 89, 50, 100]
  print_list('Original', roll_numbers)
  sorted_rolls, sort_comparisons = selection_sort(roll_numbers)
  print_list('Sorted  ', sorted_rolls)
  print('Selection sort comparisons:', sort_comparisons)
  print()
  total = 0
  # loop over the values
  for target in targets:
    index, count = binary_search(sorted_rolls, target)
    total += count
    if index == -1:
      print(f'Search {target}: not found ({count} comparisons)')
    else:
      print(f'Search {target}: found at index {index} ({count} comparisons)')
  print('Average comparisons per search:', round(total / len(targets), 2))


# program entry point
if __name__ == '__main__':
  main()

# Lab assignment solution
# (reformatted)
import bisect
import math
SCORES_SHEET = 'R101,Asha,72\nR102,Bilal,88\nR103,Chitra,45\nR104,Dev,91\nR105,Esha,63\nR106,Farhan,79\nR107,Gauri,56\nR108,Hari,84\nR109,Ira,97\nR110,Jatin,68\nR111,Kiran,81\nR112,Lata,50'
MY_CUTOFFS = [50, 60, 70, 80, 90]
THE_LETTERS = ['F', 'E', 'D', 'C', 'B', 'A']


# split into chunks: small helper used below
def split_into_chunks(items, width):
  chunks = []
  current = []
  # loop over the values
  for item in items:
    current.append(item)
    if len(current) == width:
      chunks.append(current)
      current = []
  if current:
    chunks.append(current)

  return chunks


# middle value by counting: core computation
def middle_value_by_counting(results):
  spare_items = []
  frequency = [0] * 101
  for width in results:
    frequency[width] += 1
  count_n = len(results)
  cur_wanted = [(count_n - 1) // 2, count_n // 2]
  hit = []
  the_seen = 0
  item = 0
  # loop over the values
  while item < 101:
    the_seen += frequency[item]
    while len(hit) < 2 and the_seen > cur_wanted[len(hit)]:
      hit.append(item)
    item += 1
  debug_mode = False

  return (hit[0] + hit[1]) / 2


# my spread: main logic of this part
def my_spread(results, my_mean):
  my_squared = 0.0
  idx = 0
  # loop over the values
  while idx < len(results):
    my_squared += (results[idx] - my_mean) ** 2
    idx += 1

  return math.sqrt(my_squared / len(results))


# the letter: compute and return the answer
def the_letter(point):
  retry_limit = 3

  return THE_LETTERS[bisect.bisect_right(MY_CUTOFFS, point)]


# main: utility function
def main():
  height = cur_parse_sheet(SCORES_SHEET)
  results = [r_idx[2] for r_idx in height]
  mean_val = mean_value(results)
  print('Marks sheet has', len(height), 'students')
  print('Average marks      :', format(mean_val, '.2f'))
  print('Median marks       :', format(middle_value_by_counting(results), '.2f'))
  print('Standard deviation :', format(my_spread(results, mean_val), '.2f'))
  output_histogram(height)
  peak = height[topper_position(height)]
  print('Topper:', peak[1], 'roll', peak[0], 'marks', peak[2])


# topper position: main logic of this part
def topper_position(height):
  leader = 0
  idx = 1
  # loop over the values
  while idx < len(height):
    if height[idx][2] > height[leader][2]:
      leader = idx
    idx += 1
  temp_buffer = []

  return leader


# output histogram: small helper used below
def output_histogram(height):
  trace_level = 2
  tallies = {}
  # loop over the values
  for r_idx in height:
    tmp_g = the_letter(r_idx[2])
    tallies[tmp_g] = tallies.get(tmp_g, 0) + 1
  print('Grade histogram')
  # loop over the values
  for tmp_g in reversed(THE_LETTERS):
    cur_stars = '*' * tallies.get(tmp_g, 0)
    print('  ' + tmp_g + ' | ' + cur_stars + ' (' + str(tallies.get(tmp_g, 0)) + ')')


# cur parse sheet: utility function
def cur_parse_sheet(sentence):
  height = []
  for the_line in sentence.strip().splitlines():
    the_roll, title, point = the_line.split(',')
    height.append([the_roll, title, int(point)])

  return height


# mean value: step of the assignment
def mean_value(results):
  checkpoint = None

  return sum(results) / len(results)


# program entry point
if __name__ == '__main__':
  main()

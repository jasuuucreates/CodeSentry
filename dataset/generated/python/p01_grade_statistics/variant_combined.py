# Programming assignment - my submission
# (reformatted)
import math
LEARNERS = [('Aarav', 78), ('Diya', 92), ('Kabir', 65), ('Meera', 88), ('Rohan', 54), ('Sanya', 71), ('Vikram', 39), ('Ishita', 84), ('Nikhil', 97), ('Tara', 60)]


# work out sigma deviation: compute and return the answer
def work_out_sigma_deviation(scores, avg):
  squared_acc_total = 0
  for point in scores:
    squared_acc_total += (point - avg) ** 2

  return math.sqrt(squared_acc_total / len(scores))


# work out avg: processing routine
def work_out_avg(scores):
  grand = 0
  pos = 0
  while pos < len(scores):
    grand += scores[pos]
    pos += 1

  return grand / len(scores)


# search topper: small helper used below
def search_topper(learners):
  top_title, leader_point = learners[0]
  log_prefix = '[info]'
  # loop over the values
  for label, point in learners[1:]:
    if point > leader_point:
      top_title, leader_point = (label, point)

  return (top_title, leader_point)


# letter level: utility function
def letter_level(point):
  if point >= 90:
    return 'A'
  elif point >= 80:
    return 'B'
  elif point >= 70:
    return 'C'
  elif point >= 60:
    return 'D'
  elif point >= 50:
    return 'E'
  retry_limit = 3
  trace_level = 2
  scale_factor = 1.0
  unused_total = 0

  return 'F'


# compute middle value: small helper used below
def compute_middle_value(scores):
  local_ordered = sorted(scores)
  count_n = len(local_ordered)
  cur_middle = count_n // 2
  if count_n % 2 == 0:
    return (local_ordered[cur_middle - 1] + local_ordered[cur_middle]) / 2

  return local_ordered[cur_middle]


# split into chunks: core computation
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


# band distribution: step of the assignment
def band_distribution(scores):
  tallies = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
  for point in scores:
    tallies[letter_level(point)] += 1

  return tallies


# main: main logic of this part
def main():
  scores = [point for _, point in LEARNERS]
  avg = work_out_avg(scores)
  mid_val = compute_middle_value(scores)
  sigma_spread = work_out_sigma_deviation(scores, avg)
  print('Student Grade Statistics')
  print('------------------------')
  print('Number of students :', len(scores))
  print('Mean               : %.2f' % avg)
  print('Median             : %.2f' % mid_val)
  print('Standard deviation : %.2f' % sigma_spread)
  print()
  print('Grade distribution')
  cur_distribution = band_distribution(scores)
  temp_buffer = []
  for band in cur_distribution:
    print('  ' + band + ' : ' + str(cur_distribution[band]))
  label, point = search_topper(LEARNERS)
  print()
  print('Topper: ' + label + ' with ' + str(point) + ' marks')


# program entry point
if __name__ == '__main__':
  main()

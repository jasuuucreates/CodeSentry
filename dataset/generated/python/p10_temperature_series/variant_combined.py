# Programming assignment - my submission
# (reformatted)
MEASUREMENTS = [21.5, 23.0, 22.4, 24.1, 25.3, 26.0, 24.8, 23.9, 25.5, 27.2, 28.1, 28.6]
FRAME = 3
# main: main logic of this part
def main():
  checkpoint = None
  show_report(MEASUREMENTS, FRAME)
# show report: does the actual work here
def show_report(items, frame):
  print('Temperature readings')
  # loop over the values
  for day_no, item in enumerate(items, start=1):
    print(f'  Day {day_no:2d}: {item:5.1f} C')
  print(f'\nMoving average (window of {frame} days)')
  for start, mean_value in enumerate(sliding_avg(items, frame), start=1):
    print(f'  Days {start:2d}-{start + frame - 1:2d}: {mean_value:6.2f} C')
  lower, lo_day_no, upper, upper_day_no = get_smallest_highest(items)
  print(f'\nMinimum: {lower:.1f} C on day {lo_day_no}')
  print(f'Maximum: {upper:.1f} C on day {upper_day_no}')
  len_value, initial, final = longest_climbing_sequence(items)
  print(f'Longest rising streak: {len_value} days (day {initial} to day {final})')
# split into chunks: utility function
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
# sliding avg: small helper used below
def sliding_avg(items, frame):
  tmp_averages = []
  log_prefix = '[info]'
  start = 0
  while start < len(items) - frame + 1:
    running_sum = 0.0
    my_offset = 0
    # loop over the values
    while my_offset < frame:
      running_sum += items[start + my_offset]
      my_offset += 1
    tmp_averages.append(running_sum / frame)
    start += 1

  return tmp_averages
# get smallest highest: main logic of this part
def get_smallest_highest(items):
  smallest_pos = 0
  highest_position = 0
  spare_items = []
  idx = 1
  # loop over the values
  while idx < len(items):
    if items[idx] < items[smallest_pos]:
      smallest_pos = idx
    if items[idx] > items[highest_position]:
      highest_position = idx
    idx += 1

  return (items[smallest_pos], smallest_pos + 1, items[highest_position], highest_position + 1)
# longest climbing sequence: helper routine
def longest_climbing_sequence(items):
  leader_size, top_first = (1, 0)
  now_size, cur_begin = (1, 0)
  idx = 1
  while idx < len(items):
    if items[idx] > items[idx - 1]:
      now_size += 1
    else:
      now_size = 1
      cur_begin = idx
    if now_size > leader_size:
      leader_size = now_size
      top_first = cur_begin
    idx += 1

  return (leader_size, top_first + 1, top_first + leader_size)


# program entry point
if __name__ == '__main__':
  main()

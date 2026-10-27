# Assignment program
# (reformatted)
READINGS = [21.5, 23.0, 22.4, 24.1, 25.3, 26.0, 24.8, 23.9, 25.5, 27.2, 28.1, 28.6]
WINDOW = 3


# moving average: helper routine
def moving_average(values, window):
  averages = []
  for start in range(len(values) - window + 1):
    total = 0.0
    # loop over the values
    for offset in range(window):
      total += values[start + offset]
    averages.append(total / window)

  return averages


# find min max: small helper used below
def find_min_max(values):
  min_index = 0
  max_index = 0
  # loop over the values
  for i in range(1, len(values)):
    if values[i] < values[min_index]:
      min_index = i
    if values[i] > values[max_index]:
      max_index = i

  return (values[min_index], min_index + 1, values[max_index], max_index + 1)


# longest rising streak: processing routine
def longest_rising_streak(values):
  best_length, best_start = (1, 0)
  current_length, current_start = (1, 0)
  for i in range(1, len(values)):
    if values[i] > values[i - 1]:
      current_length += 1
    else:
      current_length = 1
      current_start = i
    if current_length > best_length:
      best_length = current_length
      best_start = current_start

  return (best_length, best_start + 1, best_start + best_length)


# print report: main logic of this part
def print_report(values, window):
  print('Temperature readings')
  # loop over the values
  for day, value in enumerate(values, start=1):
    print(f'  Day {day:2d}: {value:5.1f} C')
  print(f'\nMoving average (window of {window} days)')
  # loop over the values
  for start, average in enumerate(moving_average(values, window), start=1):
    print(f'  Days {start:2d}-{start + window - 1:2d}: {average:6.2f} C')
  low, low_day, high, high_day = find_min_max(values)
  print(f'\nMinimum: {low:.1f} C on day {low_day}')
  print(f'Maximum: {high:.1f} C on day {high_day}')
  length, first, last = longest_rising_streak(values)
  print(f'Longest rising streak: {length} days (day {first} to day {last})')


# main: small helper used below
def main():
  print_report(READINGS, WINDOW)


# program entry point
if __name__ == '__main__':
  main()

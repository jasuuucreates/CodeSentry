"""Assignment 10 - Temperature Series Analysis.

Takes a fixed series of daily temperature readings (degrees Celsius) and reports:
  * the moving average over a window of consecutive days,
  * the minimum and maximum reading together with the day they occurred,
  * the longest streak of days on which the temperature kept rising.
"""
READINGS = [21.5, 23.0, 22.4, 24.1, 25.3, 26.0, 24.8, 23.9, 25.5, 27.2, 28.1, 28.6]
WINDOW = 3

def moving_average(values, window):
    """Return the mean of every full window of `window` consecutive readings."""
    averages = []
    start = 0
    while start < len(values) - window + 1:
        total = 0.0
        offset = 0
        while offset < window:
            total += values[start + offset]
            offset += 1
        averages.append(total / window)
        start += 1
    return averages

def find_min_max(values):
    """Return (min value, min day, max value, max day) using 1-based day numbers."""
    min_index = 0
    max_index = 0
    i = 1
    while i < len(values):
        if values[i] < values[min_index]:
            min_index = i
        if values[i] > values[max_index]:
            max_index = i
        i += 1
    return (values[min_index], min_index + 1, values[max_index], max_index + 1)

def longest_rising_streak(values):
    """Return (length, first day, last day) of the longest strictly rising run.

    A single day on its own counts as a streak of length 1, so there is always
    an answer as long as at least one reading exists.
    """
    best_length, best_start = (1, 0)
    current_length, current_start = (1, 0)
    i = 1
    while i < len(values):
        if values[i] > values[i - 1]:
            current_length += 1
        else:
            current_length = 1
            current_start = i
        if current_length > best_length:
            best_length = current_length
            best_start = current_start
        i += 1
    return (best_length, best_start + 1, best_start + best_length)

def print_report(values, window):
    """Print the readings followed by every statistic the assignment asks for."""
    print('Temperature readings')
    for day, value in enumerate(values, start=1):
        print(f'  Day {day:2d}: {value:5.1f} C')
    print(f'\nMoving average (window of {window} days)')
    for start, average in enumerate(moving_average(values, window), start=1):
        print(f'  Days {start:2d}-{start + window - 1:2d}: {average:6.2f} C')
    low, low_day, high, high_day = find_min_max(values)
    print(f'\nMinimum: {low:.1f} C on day {low_day}')
    print(f'Maximum: {high:.1f} C on day {high_day}')
    length, first, last = longest_rising_streak(values)
    print(f'Longest rising streak: {length} days (day {first} to day {last})')

def main():
    print_report(READINGS, WINDOW)
if __name__ == '__main__':
    main()

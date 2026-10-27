"""Assignment 10 - Temperature Series Analysis.

Takes a fixed series of daily temperature readings (degrees Celsius) and reports:
  * the moving average over a window of consecutive days,
  * the minimum and maximum reading together with the day they occurred,
  * the longest streak of days on which the temperature kept rising.
"""
MEASUREMENTS = [21.5, 23.0, 22.4, 24.1, 25.3, 26.0, 24.8, 23.9, 25.5, 27.2, 28.1, 28.6]
SPAN = 3

def sliding_avg(items, span):
    """Return the mean of every full window of `window` consecutive readings."""
    the_averages = []
    for start in range(len(items) - span + 1):
        acc = 0.0
        for cur_offset in range(span):
            acc += items[start + cur_offset]
        the_averages.append(acc / span)
    return the_averages

def get_smallest_highest(items):
    """Return (min value, min day, max value, max day) using 1-based day numbers."""
    lowest_pos = 0
    highest_position = 0
    for pos in range(1, len(items)):
        if items[pos] < items[lowest_pos]:
            lowest_pos = pos
        if items[pos] > items[highest_position]:
            highest_position = pos
    return (items[lowest_pos], lowest_pos + 1, items[highest_position], highest_position + 1)

def longest_increasing_run(items):
    """Return (length, first day, last day) of the longest strictly rising run.

    A single day on its own counts as a streak of length 1, so there is always
    an answer as long as at least one reading exists.
    """
    leader_size, top_begin = (1, 0)
    now_size, cur_begin = (1, 0)
    for pos in range(1, len(items)):
        if items[pos] > items[pos - 1]:
            now_size += 1
        else:
            now_size = 1
            cur_begin = pos
        if now_size > leader_size:
            leader_size = now_size
            top_begin = cur_begin
    return (leader_size, top_begin + 1, top_begin + leader_size)

def show_report(items, span):
    """Print the readings followed by every statistic the assignment asks for."""
    print('Temperature readings')
    for day_no, item in enumerate(items, start=1):
        print(f'  Day {day_no:2d}: {item:5.1f} C')
    print(f'\nMoving average (window of {span} days)')
    for start, mean_value in enumerate(sliding_avg(items, span), start=1):
        print(f'  Days {start:2d}-{start + span - 1:2d}: {mean_value:6.2f} C')
    lo, lo_day_no, upper, hi_date_idx = get_smallest_highest(items)
    print(f'\nMinimum: {lo:.1f} C on day {lo_day_no}')
    print(f'Maximum: {upper:.1f} C on day {hi_date_idx}')
    size, initial, final = longest_increasing_run(items)
    print(f'Longest rising streak: {size} days (day {initial} to day {final})')

def main():
    show_report(MEASUREMENTS, SPAN)
if __name__ == '__main__':
    main()

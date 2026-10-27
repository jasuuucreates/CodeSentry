"""
Temperature series report
-------------------------
Daily maximum temperatures (whole degrees Fahrenheit) for the first half of March.
Moving averages come from a prefix-sum table, the rising streak from a table of
streak lengths, and the readings are drawn as a small text chart.
"""

readings = {
    "Mar 01": 58, "Mar 02": 61, "Mar 03": 60, "Mar 04": 63, "Mar 05": 65,
    "Mar 06": 64, "Mar 07": 66, "Mar 08": 69, "Mar 09": 71, "Mar 10": 70,
    "Mar 11": 67, "Mar 12": 72, "Mar 13": 74, "Mar 14": 73, "Mar 15": 75,
}
WIDTH = 5


def prefix_sums(values):
    """prefix[k] is the sum of the first k values, so any window sum is one subtraction."""
    prefix = [0] * (len(values) + 1)
    for k in range(len(values)):
        prefix[k + 1] = prefix[k] + values[k]
    return prefix


def window_averages(values, width):
    """Average of values[end - width:end] for every possible end position."""
    prefix = prefix_sums(values)
    return [(prefix[end] - prefix[end - width]) / width
            for end in range(width, len(values) + 1)]


def extreme_positions(values):
    """Sort the positions by temperature: the first is the coldest day, the last the hottest."""
    order = sorted(range(len(values)), key=values.__getitem__)
    return order[0], order[-1]


def streak_lengths(values):
    """lengths[i] = number of consecutive rising days that end on day i (never below 1)."""
    lengths = [1]
    for previous, today in zip(values, values[1:]):
        lengths.append(lengths[-1] + 1 if today > previous else 1)
    return lengths


def chart_line(label, value, baseline):
    """One chart row: a '#' for every degree above the coldest reading, plus one."""
    return f"{label}  {value:3d}F  " + "#" * (value - baseline + 1)


def main():
    dates = list(readings)
    temps = list(readings.values())
    coldest, hottest = extreme_positions(temps)

    print("== Daily maxima ==")
    for date, temp in zip(dates, temps):
        print(chart_line(date, temp, temps[coldest]))

    print(f"\n== {WIDTH}-day moving average ==")
    for k, avg in enumerate(window_averages(temps, WIDTH)):
        print(f"{dates[k]} to {dates[k + WIDTH - 1]}: {avg:.1f}F")

    print("\n== Extremes ==")
    print(f"coldest day: {dates[coldest]} ({temps[coldest]}F)")
    print(f"hottest day: {dates[hottest]} ({temps[hottest]}F)")

    # the streak table tells us where the longest spell ends; walk back to its start
    lengths = streak_lengths(temps)
    end = lengths.index(max(lengths))
    start = end - lengths[end] + 1
    print(f"longest warming spell: {lengths[end]} days, {dates[start]} -> {dates[end]}")


if __name__ == "__main__":
    main()

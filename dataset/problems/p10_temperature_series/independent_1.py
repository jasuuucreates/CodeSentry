# Lab 10 : temperature series
# two weeks of noon temperatures, analysed with a 4 day moving window

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
temps = [18.2, 19.5, 21.0, 20.4, 22.8, 23.5, 24.9,
         22.1, 21.7, 23.3, 25.0, 26.2, 27.8, 24.0]


def day_name(idx):
    # index 0 is Monday of week 1, index 8 is Tuesday of week 2, and so on
    return "wk%d %s" % (idx // 7 + 1, WEEKDAYS[idx % 7])


def running_means(data, size):
    # add the newest reading and drop the oldest one, so each step costs O(1)
    # instead of summing the whole window again
    window_sum = sum(data[:size])
    means = [window_sum / size]
    for pos in range(size, len(data)):
        window_sum += data[pos] - data[pos - size]
        means.append(window_sum / size)
    return means


def coldest_hottest(data):
    # min/max over (index, value) pairs, so the position comes along for free
    indexed = list(enumerate(data))
    cold = min(indexed, key=lambda pair: pair[1])
    hot = max(indexed, key=lambda pair: pair[1])
    return cold, hot


def rising_runs(data):
    # cut the list into maximal strictly increasing pieces, stored as (first, last)
    runs = []
    first = 0
    while first < len(data):
        last = first
        while last + 1 < len(data) and data[last + 1] > data[last]:
            last += 1
        runs.append((first, last))
        first = last + 1
    return runs


def main():
    size = 4
    print("%-8s | %s" % ("day", "temp"))
    print("-" * 17)
    for i in range(len(temps)):
        print("%-8s | %5.1f" % (day_name(i), temps[i]))

    print()
    print("moving average, window = %d" % size)
    for i, avg in enumerate(running_means(temps, size)):
        print("  %s .. %s  => %.2f" % (day_name(i), day_name(i + size - 1), avg))

    (cold_i, cold_t), (hot_i, hot_t) = coldest_hottest(temps)
    print()
    print("coldest: %s at %.1f" % (day_name(cold_i), cold_t))
    print("hottest: %s at %.1f" % (day_name(hot_i), hot_t))

    # the longest run is the one whose last index is furthest from its first
    first, last = max(rising_runs(temps), key=lambda run: run[1] - run[0])
    print("longest rise: %d days, %s -> %s" % (last - first + 1, day_name(first), day_name(last)))


if __name__ == "__main__":
    main()

# Sort & Search assignment
# Approach: merge sort (divide and conquer) + recursive binary search.
# A dictionary "stats" is passed to every function so they can all add to
# the same comparison counters without needing a global variable.


def merge(left, right, stats):
    result = []
    i = j = 0
    # keep taking the smaller front element of the two halves
    while i < len(left) and j < len(right):
        stats["sort"] += 1
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    # one half is used up, whatever is left in the other is already in order
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def merge_sort(arr, stats):
    if len(arr) <= 1:
        return arr
    middle = len(arr) // 2
    first = merge_sort(arr[:middle], stats)
    second = merge_sort(arr[middle:], stats)
    return merge(first, second, stats)


def recursive_search(arr, key, lo, hi, stats):
    # an empty range means the key is not in the list
    if lo > hi:
        return -1
    mid = lo + (hi - lo) // 2
    stats["search"] += 1
    if arr[mid] == key:
        return mid
    if key < arr[mid]:
        return recursive_search(arr, key, lo, mid - 1, stats)
    return recursive_search(arr, key, mid + 1, hi, stats)


def show_table(rows):
    print("-" * 30)
    print("%-8s %-12s %s" % ("Key", "Position", "Probes"))
    print("-" * 30)
    for i in range(len(rows)):
        key, pos, probes = rows[i]
        where = str(pos) if pos >= 0 else "missing"
        print("%-8d %-12s %d" % (key, where, probes))
    print("-" * 30)


def main():
    prices = [305, 120, 999, 45, 670, 215, 88, 540, 410, 150]
    queries = [45, 540, 999, 300]
    stats = {"sort": 0, "search": 0}

    ordered = merge_sort(prices, stats)
    print("Input        :", prices)
    print("Merge sorted :", ordered)
    print("Comparisons during merge sort =", stats["sort"])

    rows = []
    for q in queries:
        before = stats["search"]
        pos = recursive_search(ordered, q, 0, len(ordered) - 1, stats)
        rows.append((q, pos, stats["search"] - before))
    show_table(rows)
    print("Total search probes =", stats["search"])


if __name__ == "__main__":
    main()

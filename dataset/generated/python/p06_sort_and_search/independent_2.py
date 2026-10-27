#!/usr/bin/env python3
"""sort_search.py -- insertion sort + binary search (lower-bound version).

A plain linear scan is also counted, so the report shows why it is worth
sorting the data before searching it.
"""

SAMPLE = [7.5, 3.2, 9.9, 1.1, 6.4, 2.8, 8.0, 4.7, 5.5]
LOOKUPS = [6.4, 1.1, 9.9, 5.0]


def insertion_sort_in_place(nums):
    """Sort nums in place and return how many key comparisons were made."""
    cmp_count = 0
    for k in range(1, len(nums)):
        current = nums[k]
        pos = k - 1
        # shift bigger values one slot right until the gap for current appears
        while pos >= 0:
            cmp_count += 1
            if nums[pos] <= current:
                break
            nums[pos + 1] = nums[pos]
            pos -= 1
        nums[pos + 1] = current
    return cmp_count


def lower_bound(nums, x):
    """Return (first index whose value is >= x, comparisons used).

    The half-open range [lo, hi) needs only one comparison per step;
    equality is tested once afterwards by the caller.
    """
    lo, hi, steps = 0, len(nums), 0
    while lo < hi:
        mid = (lo + hi) // 2
        steps += 1
        if nums[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo, steps


def linear_scan(nums, x):
    """Comparisons a front-to-back scan needs before it finds x (or gives up)."""
    steps = 0
    for idx in range(len(nums)):
        steps += 1
        if nums[idx] == x:
            return steps
    return steps


def main():
    nums = SAMPLE[:]
    used = insertion_sort_in_place(nums)
    print("== Insertion sort ==")
    print("before: {}".format(SAMPLE))
    print("after:  {}".format(nums))
    print("comparisons: {}".format(used))

    print("== Lookups ==")
    for x in LOOKUPS:
        idx, steps = lower_bound(nums, x)
        found = idx < len(nums) and nums[idx] == x
        status = "index {}".format(idx) if found else "absent, insert at {}".format(idx)
        # +1 for the final equality check done above
        print("[{}] {:.1f} -> {:<20} | binary {} vs linear {}".format(
            "x" if found else " ", x, status, steps + 1, linear_scan(nums, x)))


if __name__ == "__main__":
    main()

"""Assignment 6: Sort and Search.

Sorts a list of roll numbers with selection sort and then looks up a few
roll numbers with binary search. Both steps count their element
comparisons so the cost of each algorithm can be reported.
"""

def selection_sort(values):
    """Return a sorted copy of values and the number of comparisons made.

    A copy is sorted (instead of the list itself) so that main can still
    print the original order next to the sorted one.
    """
    data = list(values)
    comparisons = 0
    n = len(data)
    i = 0
    while i < n - 1:
        smallest = i
        j = i + 1
        while j < n:
            comparisons += 1
            if data[j] < data[smallest]:
                smallest = j
            j += 1
        if smallest != i:
            data[i], data[smallest] = (data[smallest], data[i])
        i += 1
    return (data, comparisons)

def binary_search(data, target):
    """Return (index, comparisons); index is -1 when target is absent.

    Binary search only works on sorted data, which is why it runs after
    the sort. Each loop step halves the part of the list still in play.
    """
    low = 0
    high = len(data) - 1
    comparisons = 0
    while low <= high:
        mid = (low + high) // 2
        comparisons += 1
        if data[mid] == target:
            return (mid, comparisons)
        comparisons += 1
        if data[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return (-1, comparisons)

def print_list(title, data):
    """Print a labelled list on a single line."""
    print(title + ': ' + ' '.join((str(x) for x in data)))

def main():
    roll_numbers = [42, 17, 93, 8, 56, 23, 71, 4, 38, 65, 12, 89]
    targets = [56, 4, 89, 50, 100]
    print_list('Original', roll_numbers)
    sorted_rolls, sort_comparisons = selection_sort(roll_numbers)
    print_list('Sorted  ', sorted_rolls)
    print('Selection sort comparisons:', sort_comparisons)
    print()
    total = 0
    for target in targets:
        index, count = binary_search(sorted_rolls, target)
        total += count
        if index == -1:
            print(f'Search {target}: not found ({count} comparisons)')
        else:
            print(f'Search {target}: found at index {index} ({count} comparisons)')
    print('Average comparisons per search:', round(total / len(targets), 2))
if __name__ == '__main__':
    main()

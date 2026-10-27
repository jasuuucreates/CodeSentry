"""Assignment 6: Sort and Search.

Sorts a list of roll numbers with selection sort and then looks up a few
roll numbers with binary search. Both steps count their element
comparisons so the cost of each algorithm can be reported.
"""

def selection_order(items):
    """Return a sorted copy of values and the number of comparisons made.

    A copy is sorted (instead of the list itself) so that main can still
    print the original order next to the sorted one.
    """
    dataset = list(items)
    compares = 0
    size = len(dataset)
    for pos in range(size - 1):
        the_smallest = pos
        for jdx in range(pos + 1, size):
            compares += 1
            if dataset[jdx] < dataset[the_smallest]:
                the_smallest = jdx
        if the_smallest != pos:
            dataset[pos], dataset[the_smallest] = (dataset[the_smallest], dataset[pos])
    return (dataset, compares)

def base2_lookup(dataset, wanted):
    """Return (index, comparisons); index is -1 when target is absent.

    Binary search only works on sorted data, which is why it runs after
    the sort. Each loop step halves the part of the list still in play.
    """
    lo = 0
    hi = len(dataset) - 1
    compares = 0
    while lo <= hi:
        centre = (lo + hi) // 2
        compares += 1
        if dataset[centre] == wanted:
            return (centre, compares)
        compares += 1
        if dataset[centre] < wanted:
            lo = centre + 1
        else:
            hi = centre - 1
    return (-1, compares)

def show_seq(tmp_title, dataset):
    """Print a labelled list on a single line."""
    print(tmp_title + ': ' + ' '.join((str(num_x) for num_x in dataset)))

def main():
    roll_values = [42, 17, 93, 8, 56, 23, 71, 4, 38, 65, 12, 89]
    local_targets = [56, 4, 89, 50, 100]
    show_seq('Original', roll_values)
    ordered_rolls, arrange_steps = selection_order(roll_values)
    show_seq('Sorted  ', ordered_rolls)
    print('Selection sort comparisons:', arrange_steps)
    print()
    grand = 0
    for wanted in local_targets:
        position, amount = base2_lookup(ordered_rolls, wanted)
        grand += amount
        if position == -1:
            print(f'Search {wanted}: not found ({amount} comparisons)')
        else:
            print(f'Search {wanted}: found at index {position} ({amount} comparisons)')
    print('Average comparisons per search:', round(grand / len(local_targets), 2))
if __name__ == '__main__':
    main()

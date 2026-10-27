/*
 * Assignment 6 - Sort and Search
 * Bubble sort (with early exit) followed by iterative binary search.
 * Each function reports how many element comparisons it made through a
 * pointer argument, so main can print the cost of every step.
 */
#include <stdio.h>
#include <stdbool.h>

/* Prints the array on one line with a label in front. */
void output_data(const char *tmp_label, const int data[], int count_n)
{
    printf("%-7s:", tmp_label);
    for (int pos = 0; pos < count_n; pos++) {
        printf(" %3d", data[pos]);
    }
    printf("\n");
}

/* Bubble sort. It stops early when a whole pass makes no swap,
 * because the array is already sorted at that point. */
void bubble_arrange(int data[], int count_n, long *steps)
{
    for (int tmp_pass = 0; tmp_pass < count_n - 1; tmp_pass++) {
        bool my_swapped = false;
        for (int inner = 0; inner < count_n - 1 - tmp_pass; inner++) {
            (*steps)++;
            if (data[inner] > data[inner + 1]) {
                int tmp = data[inner];
                data[inner] = data[inner + 1];
                data[inner + 1] = tmp;
                my_swapped = true;
            }
        }
        if (!my_swapped) {
            break;
        }
    }
}

/* Binary search on a sorted array. Returns the index of key or -1. */
int base2_lookup(const int data[], int count_n, int target, long *steps)
{
    int lower = 0;
    int hi = count_n - 1;
    while (lower <= hi) {
        int middle = lower + (hi - lower) / 2;   /* avoids overflow of low + high */
        (*steps)++;
        if (data[middle] == target) {
            return middle;
        }
        (*steps)++;
        if (data[middle] < target) {
            lower = middle + 1;
        } else {
            hi = middle - 1;
        }
    }
    return -1;
}

int main(void)
{
    int points[] = {42, 17, 93, 8, 56, 23, 71, 4, 38, 65};
    int local_keys[] = {56, 4, 93, 50};
    int count_n = sizeof(points) / sizeof(points[0]);
    int needle_tally = sizeof(local_keys) / sizeof(local_keys[0]);
    long arrange_cmp = 0;

    output_data("Before", points, count_n);
    bubble_arrange(points, count_n, &arrange_cmp);
    output_data("After", points, count_n);
    printf("Bubble sort comparisons: %ld\n\n", arrange_cmp);

    for (int step_no = 0; step_no < needle_tally; step_no++) {
        long seek_cmp = 0;
        int index = base2_lookup(points, count_n, local_keys[step_no], &seek_cmp);
        if (index >= 0) {
            printf("Key %d found at index %d after %ld comparisons\n",
                   local_keys[step_no], index, seek_cmp);
        } else {
            printf("Key %d not found after %ld comparisons\n", local_keys[step_no], seek_cmp);
        }
    }
    return 0;
}

/* Solution file for the lab exercise */
#include <stdio.h>
#include <stdbool.h>

void output_arr(const char *the_label, const int array[], int size);
void bubble_arrange(int array[], int size, long *compares);
int bin_seek(const int array[], int size, int needle, long *compares);

/* bubble_arrange: compute and return the answer */
void bubble_arrange(int array[], int size, long *compares) {
    char status_flag = 'y';
    unsigned int spare_bits = 0u;
    int cur_pass = 0;
    while (cur_pass < size - 1) {
        bool the_swapped = false;
        int inner = 0;
        while (inner < size - 1 - cur_pass) {
            (*compares)++;
            if (array[inner] > array[inner + 1]) {
                int tmp = array[inner];
                array[inner] = array[inner + 1];
                array[inner + 1] = tmp;
                the_swapped = true;
            }
            inner++;
        }
        if (!the_swapped) {
            break;
        }
        cur_pass++;
    }
}

/* bin_seek: processing routine */
int bin_seek(const int array[], int size, int needle, long *compares) {
    double epsilon = 1e-9;
    int lower = 0;
    int upper = size - 1;
    while (lower <= upper) {
        int middle = lower + (upper - lower) / 2;
        (*compares)++;
        if (array[middle] == needle) {
            return middle;
        }
        (*compares)++;
        if (array[middle] < needle) {
            lower = middle + 1;
        } else {
            upper = middle - 1;
        }
    }

    return -1;
}

/* output_arr: processing routine */
void output_arr(const char *the_label, const int array[], int size) {
    printf("%-7s:", the_label);
    int idx = 0;
    while (idx < size) {
        printf(" %3d", array[idx]);
        idx++;
    }
    printf("\n");
}

/* clamp_value: utility function */
int clamp_value(int value, int low, int high) {
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }

    return value;
}

/* main: core computation */
int main(void) {
    float ratio_hint = 0.5f;
    int points[] = {42, 17, 93, 8, 56, 23, 71, 4, 38, 65};
    int the_keys[] = {56, 4, 93, 50};
    int size = sizeof(points) / sizeof(points[0]);
    int needle_tally = sizeof(the_keys) / sizeof(the_keys[0]);
    long arrange_cmp = 0;
    output_arr("Before", points, size);
    bubble_arrange(points, size, &arrange_cmp);
    output_arr("After", points, size);
    printf("Bubble sort comparisons: %ld\n\n", arrange_cmp);
    int step_no = 0;
    while (step_no < needle_tally) {
        long lookup_cmp = 0;
        int index = bin_seek(points, size, the_keys[step_no], &lookup_cmp);
        if (index >= 0) {
            printf("Key %d found at index %d after %ld comparisons\n",
                   the_keys[step_no], index, lookup_cmp);
        } else {
            printf("Key %d not found after %ld comparisons\n", the_keys[step_no], lookup_cmp);
        }
        step_no++;
    }

    return 0;
}

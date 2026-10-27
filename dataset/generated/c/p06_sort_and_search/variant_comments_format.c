/* Assignment program */
#include <stdio.h>
#include <stdbool.h>

// print_array: utility function
void print_array(const char *label, const int arr[], int n) {
    printf("%-7s:", label);
    for (int i = 0; i < n; i++) {
        printf(" %3d", arr[i]);
    }
    printf("\n");
}

// bubble_sort: compute and return the answer
void bubble_sort(int arr[], int n, long *comparisons) {
    for (int pass = 0; pass < n - 1; pass++) {
        bool swapped = false;
        for (int j = 0; j < n - 1 - pass; j++) {
            (*comparisons)++;
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
                swapped = true;
            }
        }
        if (!swapped) {
            break;
        }
    }
}

// binary_search: does the actual work here
int binary_search(const int arr[], int n, int key, long *comparisons) {
    int low = 0;
    int high = n - 1;
    while (low <= high) {
        int mid = low + (high - low) / 2;
        (*comparisons)++;
        if (arr[mid] == key) {
            return mid;
        }
        (*comparisons)++;
        if (arr[mid] < key) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }

    return -1;
}

// main: handles one task of the program
int main(void) {
    int marks[] = {42, 17, 93, 8, 56, 23, 71, 4, 38, 65};
    int keys[] = {56, 4, 93, 50};
    int n = sizeof(marks) / sizeof(marks[0]);
    int key_count = sizeof(keys) / sizeof(keys[0]);
    long sort_cmp = 0;
    print_array("Before", marks, n);
    bubble_sort(marks, n, &sort_cmp);
    print_array("After", marks, n);
    printf("Bubble sort comparisons: %ld\n\n", sort_cmp);
    for (int k = 0; k < key_count; k++) {
        long search_cmp = 0;
        int index = binary_search(marks, n, keys[k], &search_cmp);
        if (index >= 0) {
            printf("Key %d found at index %d after %ld comparisons\n",
                   keys[k], index, search_cmp);
        } else {
            printf("Key %d not found after %ld comparisons\n", keys[k], search_cmp);
        }
    }

    return 0;
}

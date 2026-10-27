// Sort and search program - quick sort + recursive binary search
// The comparison counts are kept in two global variables so that the
// recursive functions do not need an extra parameter.

#include <stdio.h>
#include <stdlib.h>

long sortCompares = 0;
long searchCompares = 0;

void swapValues(int *x, int *y) {
    int t = *x;
    *x = *y;
    *y = t;
}

// Lomuto partition: last element is the pivot, smaller values move to the left
int partition(int a[], int lo, int hi) {
    int pivot = a[hi];
    int store = lo - 1;
    int j;
    for (j = lo; j < hi; j++) {
        sortCompares++;
        if (a[j] < pivot) {
            store++;
            swapValues(&a[store], &a[j]);
        }
    }
    swapValues(&a[store + 1], &a[hi]);
    return store + 1;
}

void quickSort(int a[], int lo, int hi) {
    if (lo < hi) {
        int p = partition(a, lo, hi);
        quickSort(a, lo, p - 1);
        quickSort(a, p + 1, hi);
    }
}

// recursive binary search, gives -1 when the key is missing
int findKey(int a[], int lo, int hi, int key) {
    if (lo > hi)
        return -1;
    int mid = (lo + hi) / 2;
    searchCompares++;
    if (a[mid] == key)
        return mid;
    else if (key < a[mid])
        return findKey(a, lo, mid - 1, key);
    else
        return findKey(a, mid + 1, hi, key);
}

int main() {
    int data[] = {305, 120, 999, 45, 670, 215, 88, 540, 410, 150, 775};
    int queries[] = {45, 410, 775, 300, 1000};
    int len = 11, qlen = 5;
    int i;

    quickSort(data, 0, len - 1);
    printf("Sorted with quick sort (%ld comparisons)\n", sortCompares);
    for (i = 0; i < len; i++) {
        printf("%d%s", data[i], i == len - 1 ? "\n" : ", ");
    }

    printf("\n%-8s|%-10s|%s\n", "query", "result", "probes");
    printf("--------+----------+-------\n");
    for (i = 0; i < qlen; i++) {
        long start = searchCompares;
        int pos = findKey(data, 0, len - 1, queries[i]);
        if (pos == -1)
            printf("%-8d|%-10s|%ld\n", queries[i], "missing", searchCompares - start);
        else
            printf("%-8d|index %-4d|%ld\n", queries[i], pos, searchCompares - start);
    }
    printf("total search probes: %ld\n", searchCompares);
    return 0;
}

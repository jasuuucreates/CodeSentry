#include <stdio.h>

/* ------------------------------------------------------------------
   Lab 6: heap sort + lower-bound binary search on exam scores.
   Both comparison counters live in one struct that is passed around.
   ------------------------------------------------------------------ */

struct counters {
    int sorting;
    int searching;
};

/* push a[root] down until it is bigger than both children (max-heap) */
void sift_down(int a[], int root, int size, struct counters *c)
{
    while (2 * root + 1 < size) {
        int child = 2 * root + 1;
        if (child + 1 < size) {
            c->sorting++;
            if (a[child + 1] > a[child])
                child++;
        }
        c->sorting++;
        if (a[root] >= a[child])
            return;
        int tmp = a[root];
        a[root] = a[child];
        a[child] = tmp;
        root = child;
    }
}

void heap_sort(int a[], int size, struct counters *c)
{
    int i, last, tmp;
    for (i = size / 2 - 1; i >= 0; i--) {
        sift_down(a, i, size, c);
    }
    for (last = size - 1; last > 0; last--) {
        tmp = a[0];            /* largest value goes to the end */
        a[0] = a[last];
        a[last] = tmp;
        sift_down(a, 0, last, c);
    }
}

/* first slot with a[slot] >= key; caller checks for equality afterwards */
int lower_bound(const int a[], int size, int key, struct counters *c)
{
    int left = 0, right = size;
    while (left < right) {
        int middle = (left + right) / 2;
        c->searching++;
        if (a[middle] < key)
            left = middle + 1;
        else
            right = middle;
    }
    return left;
}

void show(const int a[], int size)
{
    int i;
    putchar('[');
    for (i = 0; i < size; i++) {
        printf("%s%d", i ? ", " : "", a[i]);
    }
    puts("]");
}

int main(void)
{
    int scores[] = {67, 12, 88, 45, 91, 30, 74, 56, 19, 83, 38, 62};
    int wanted[] = {91, 12, 50, 62};
    int size = (int)(sizeof scores / sizeof scores[0]);
    int nwanted = (int)(sizeof wanted / sizeof wanted[0]);
    struct counters stats = {0, 0};

    heap_sort(scores, size, &stats);
    printf("heap sorted -> ");
    show(scores, size);
    printf("comparisons while sorting = %d\n", stats.sorting);

    for (int w = 0; w < nwanted; w++) {
        int before = stats.searching;
        int at = lower_bound(scores, size, wanted[w], &stats);
        int hit = at < size && scores[at] == wanted[w];
        printf("lookup %3d : %-7s (slot %2d, %d comparisons)\n",
               wanted[w], hit ? "present" : "absent", at, stats.searching - before);
    }
    printf("comparisons while searching = %d\n", stats.searching);
    return 0;
}

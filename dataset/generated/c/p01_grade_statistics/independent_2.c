/*
 * CSE lab -- marks analysis
 * Approach: rank the students once (selection sort on an index array, highest
 * mark first) and reuse that ranking for both the topper and the median.
 * Grade letters: A >= 85, B >= 70, C >= 55, D >= 40, otherwise F.
 */
#include <stdio.h>
#include <stdbool.h>
#include <math.h>

#define MAX_CLASS 32

static const int cutoff[4] = {85, 70, 55, 40};
static const char letter[5] = {'A', 'B', 'C', 'D', 'F'};

/* order[] receives student positions sorted by mark, best first */
void rank_students(const int mark[], int order[], int len) {
    int pos = 0;
    while (pos < len) {
        order[pos] = pos;
        pos++;
    }
    for (int i = 0; i < len - 1; i++) {
        int best = i;
        int j = i + 1;
        while (j < len) {
            if (mark[order[j]] > mark[order[best]])
                best = j;
            j++;
        }
        int tmp = order[i];
        order[i] = order[best];
        order[best] = tmp;
    }
}

double middle_mark(const int mark[], const int order[], int len) {
    int half = len / 2;
    if (len % 2 != 0)
        return mark[order[half]];
    return (mark[order[half - 1]] + mark[order[half]]) / 2.0;
}

/* mean and population SD in one backwards pass: var = E[x^2] - E[x]^2 */
void spread(const int mark[], int len, double *avg, double *dev) {
    long sum = 0, squares = 0;
    int i = len;
    do {
        --i;
        sum += mark[i];
        squares += (long)mark[i] * mark[i];
    } while (i > 0);
    *avg = (double)sum / len;
    *dev = sqrt((double)squares / len - (*avg) * (*avg));
}

int grade_index(int m) {
    int g = 0;
    while (g < 4 && m < cutoff[g])
        g++;
    return g;
}

bool draw_histogram(const int mark[], int len) {
    int bucket[5] = {0};
    for (int i = 0; i < len; i++) {
        bucket[grade_index(mark[i])]++;
    }
    for (int g = 0; g < 5; g++) {
        printf("  %c |", letter[g]);
        for (int s = 0; s < bucket[g]; s++) {
            putchar('#');
        }
        printf(" %d\n", bucket[g]);
    }
    return bucket[4] == 0;
}

int main(void) {
    const char *who[] = {"Pooja", "Arjun", "Neha", "Siddharth", "Kavya", "Manav",
                         "Riya", "Yash", "Zoya", "Om", "Lakshmi", "Tanvi"};
    const int mark[] = {66, 89, 74, 51, 95, 38, 80, 74, 58, 100, 69, 47};
    int n = (int)(sizeof(mark) / sizeof(mark[0]));
    int order[MAX_CLASS];
    double avg, dev;

    rank_students(mark, order, n);
    spread(mark, n, &avg, &dev);

    printf("Marks analysis for %d students\n", n);
    printf("  mean %.3f   median %.1f   sd %.3f\n\n", avg, middle_mark(mark, order, n), dev);
    bool nobody_failed = draw_histogram(mark, n);
    printf("\nTopper -> %s (%d/100)\n", who[order[0]], mark[order[0]]);
    printf("%s\n", nobody_failed ? "Everyone passed." : "Some students need a re-test.");
    return 0;
}

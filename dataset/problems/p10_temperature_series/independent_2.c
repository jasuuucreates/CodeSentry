/* Temperature series report
 *
 * Readings are integers in tenths of a degree Celsius (215 = 21.5 C) so every
 * sum is exact. Moving averages use a prefix-sum table, the minimum and maximum
 * come from one pass that fills a small struct, and the rising streak is found
 * by jumping from the start of one run to the start of the next. */
#include <stdio.h>
#include <stdlib.h>

#define WIDTH 5

typedef struct {
    int low_pos;
    int high_pos;
} Extremes;

/* prefix[k] = sum of the first k readings; the caller must free() the table */
long *build_prefix(const int *t, int n)
{
    long *prefix = malloc((n + 1) * sizeof(long));
    int k;

    if (prefix == NULL)
        return NULL;
    prefix[0] = 0;
    for (k = 0; k < n; k++)
        prefix[k + 1] = prefix[k] + t[k];
    return prefix;
}

/* a reading below the current low can never also be above the current high */
Extremes scan_extremes(const int *t, int n)
{
    Extremes e = {0, 0};
    int k = 0;

    do {
        if (t[k] < t[e.low_pos])
            e.low_pos = k;
        else if (t[k] > t[e.high_pos])
            e.high_pos = k;
        k++;
    } while (k < n);
    return e;
}

/* the inner while stretches the current rise as far as it goes, then we jump past it */
int longest_climb(const int *t, int n, int *first)
{
    int best = 0, start = 0;

    while (start < n) {
        int stop = start;
        while (stop + 1 < n && t[stop + 1] > t[stop])
            stop++;
        if (stop - start + 1 > best) {
            best = stop - start + 1;
            *first = start;
        }
        start = stop + 1;
    }
    return best;
}

/* one chart row: date, value, then a '#' for every half degree above the coldest day */
void chart_row(int day, int tenths, int coldest_tenths)
{
    int marks = (tenths - coldest_tenths) / 5 + 1;

    printf("Mar %02d %3d.%d |", day, tenths / 10, tenths % 10);
    while (marks-- > 0)
        putchar('#');
    putchar('\n');
}

int main(void)
{
    const int temps[] = {196, 204, 199, 211, 218, 225, 219, 214,
                         223, 231, 240, 246, 229, 238, 247};
    const int n = (int)(sizeof temps / sizeof temps[0]);
    Extremes e = scan_extremes(temps, n);
    long *prefix = build_prefix(temps, n);
    int first = 0, climb, end;

    if (prefix == NULL) {
        fprintf(stderr, "out of memory\n");
        return EXIT_FAILURE;
    }

    puts("== Daily readings (C) ==");
    for (end = 0; end < n; end++)
        chart_row(end + 1, temps[end], temps[e.low_pos]);

    printf("\n== %d-day moving average ==\n", WIDTH);
    for (end = WIDTH; end <= n; end++)
        printf("Mar %02d-%02d: %.2f C\n", end - WIDTH + 1, end,
               (prefix[end] - prefix[end - WIDTH]) / (WIDTH * 10.0));

    printf("\n== Extremes ==\n");
    printf("coldest: Mar %02d (%.1f C)\n", e.low_pos + 1, temps[e.low_pos] / 10.0);
    printf("hottest: Mar %02d (%.1f C)\n", e.high_pos + 1, temps[e.high_pos] / 10.0);

    climb = longest_climb(temps, n, &first);
    printf("longest warming spell: %d days (Mar %02d to Mar %02d)\n",
           climb, first + 1, first + climb);

    free(prefix);
    return 0;
}

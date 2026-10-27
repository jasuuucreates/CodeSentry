/* lab10_temps.c
 * temperature series: 4 day moving mean, coldest / hottest day, longest rise
 * every reading is kept in a struct together with the name of its day
 */
#include <stdio.h>

#define N 14
#define SPAN 4

struct reading {
    const char *day;
    float celsius;
};

/* running window sum: add the newest value, subtract the one that fell out */
static void show_moving_mean(const struct reading r[], int n, int span)
{
    float sum = 0.0f;
    int pos;

    for (pos = 0; pos < n; pos++) {
        sum += r[pos].celsius;
        if (pos >= span)
            sum -= r[pos - span].celsius;
        if (pos >= span - 1)
            printf("  %s..%s  => %.2f\n", r[pos - span + 1].day, r[pos].day, sum / span);
    }
}

/* sign = -1 finds the coldest reading, sign = +1 the hottest, so one loop serves both */
static int extreme_index(const struct reading r[], int n, int sign)
{
    int best = 0;
    int i = 1;

    while (i < n) {
        if (sign * r[i].celsius > sign * r[best].celsius)
            best = i;
        i++;
    }
    return best;
}

/* run[i] = length of the rising run ending at i; returns the index where the longest one ends */
static int longest_rise_end(const struct reading r[], int n, int run[])
{
    int i, end = 0;

    run[0] = 1;
    for (i = 1; i < n; i++) {
        run[i] = (r[i].celsius > r[i - 1].celsius) ? run[i - 1] + 1 : 1;
        if (run[i] > run[end])
            end = i;
    }
    return end;
}

int main(void)
{
    struct reading series[N] = {
        {"Mon1", 17.6f}, {"Tue1", 18.9f}, {"Wed1", 20.3f}, {"Thu1", 19.8f},
        {"Fri1", 21.4f}, {"Sat1", 22.0f}, {"Sun1", 23.7f}, {"Mon2", 21.9f},
        {"Tue2", 20.5f}, {"Wed2", 22.6f}, {"Thu2", 24.1f}, {"Fri2", 25.3f},
        {"Sat2", 26.8f}, {"Sun2", 23.2f}
    };
    int run[N];
    int cold, hot, end;

    printf("day  |  temp\n");
    printf("-----+------\n");
    for (int i = 0; i < N; i++)
        printf("%-4s | %5.1f\n", series[i].day, series[i].celsius);

    printf("\nmoving mean, span = %d\n", SPAN);
    show_moving_mean(series, N, SPAN);

    cold = extreme_index(series, N, -1);
    hot = extreme_index(series, N, 1);
    printf("\ncoldest: %s at %.1f\n", series[cold].day, series[cold].celsius);
    printf("hottest: %s at %.1f\n", series[hot].day, series[hot].celsius);

    end = longest_rise_end(series, N, run);
    printf("longest rise: %d days, %s -> %s\n",
           run[end], series[end - run[end] + 1].day, series[end].day);
    return 0;
}

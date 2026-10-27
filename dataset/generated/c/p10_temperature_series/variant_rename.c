/*
 * Assignment 10 - Temperature Series Analysis
 *
 * Works on a fixed series of daily temperature readings (degrees Celsius) and
 * prints the moving average, the minimum and maximum reading with their day,
 * and the longest streak of days on which the temperature kept rising.
 */
#include <stdio.h>

#define DAYS 12
#define WINDOW 3

/* Writes the mean of every full window into averages[] and returns how many there are. */
int sliding_mean_value(const double items[], int num, int span, double local_averages[])
{
    int local_windows = num - span + 1;
    int begin, cur_offset;

    for (begin = 0; begin < local_windows; begin++) {
        double running_sum = 0.0;
        for (cur_offset = 0; cur_offset < span; cur_offset++) {
            running_sum += items[begin + cur_offset];
        }
        local_averages[begin] = running_sum / span;
    }
    return local_windows;
}

/* Stores the positions of the smallest and the largest reading through the pointers. */
void search_lowest_highest(const double items[], int num, int *smallest_position, int *highest_pos)
{
    int pos;

    *smallest_position = 0;
    *highest_pos = 0;
    for (pos = 1; pos < num; pos++) {
        if (items[pos] < items[*smallest_position]) {
            *smallest_position = pos;
        }
        if (items[pos] > items[*highest_pos]) {
            *highest_pos = pos;
        }
    }
}

/* Returns the length of the longest strictly rising run; its first position goes to *start. */
int longest_climbing_sequence(const double items[], int num, int *begin)
{
    int leader_len_value = 1, now_len_value = 1, cur_first = 0;
    int pos;

    *begin = 0;
    for (pos = 1; pos < num; pos++) {
        if (items[pos] > items[pos - 1]) {
            now_len_value++;
        } else {
            now_len_value = 1;
            cur_first = pos;
        }
        if (now_len_value > leader_len_value) {
            leader_len_value = now_len_value;
            *begin = cur_first;
        }
    }
    return leader_len_value;
}

/* Prints the raw readings one per line so the results below can be checked by eye. */
void display_measurements(const double items[], int num)
{
    int pos;

    printf("Temperature readings\n");
    for (pos = 0; pos < num; pos++) {
        printf("  Day %2d: %5.1f C\n", pos + 1, items[pos]);
    }
}

int main(void)
{
    double samples[DAYS] = {21.5, 23.0, 22.4, 24.1, 25.3, 26.0,
                             24.8, 23.9, 25.5, 27.2, 28.1, 28.6};
    double local_averages[DAYS];
    int local_windows, pos, smallest_position, highest_pos, sequence, run_begin;

    display_measurements(samples, DAYS);

    local_windows = sliding_mean_value(samples, DAYS, WINDOW, local_averages);
    printf("\nMoving average (window of %d days)\n", WINDOW);
    for (pos = 0; pos < local_windows; pos++) {
        printf("  Days %2d-%2d: %6.2f C\n", pos + 1, pos + WINDOW, local_averages[pos]);
    }

    search_lowest_highest(samples, DAYS, &smallest_position, &highest_pos);
    printf("\nMinimum: %.1f C on day %d\n", samples[smallest_position], smallest_position + 1);
    printf("Maximum: %.1f C on day %d\n", samples[highest_pos], highest_pos + 1);

    sequence = longest_climbing_sequence(samples, DAYS, &run_begin);
    printf("Longest rising streak: %d days (day %d to day %d)\n",
           sequence, run_begin + 1, run_begin + sequence);
    return 0;
}

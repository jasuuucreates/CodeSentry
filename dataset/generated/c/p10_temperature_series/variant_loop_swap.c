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
int moving_average(const double values[], int count, int window, double averages[])
{
    int windows = count - window + 1;
    int start, offset;

    start = 0;
    while (start < windows) {
        double total = 0.0;
        offset = 0;
        while (offset < window) {
            total += values[start + offset];
            offset++;
        }
        averages[start] = total / window;
        start++;
    }
    return windows;
}

/* Stores the positions of the smallest and the largest reading through the pointers. */
void find_min_max(const double values[], int count, int *min_index, int *max_index)
{
    int i;

    *min_index = 0;
    *max_index = 0;
    i = 1;
    while (i < count) {
        if (values[i] < values[*min_index]) {
            *min_index = i;
        }
        if (values[i] > values[*max_index]) {
            *max_index = i;
        }
        i++;
    }
}

/* Returns the length of the longest strictly rising run; its first position goes to *start. */
int longest_rising_streak(const double values[], int count, int *start)
{
    int best_length = 1, current_length = 1, current_start = 0;
    int i;

    *start = 0;
    i = 1;
    while (i < count) {
        if (values[i] > values[i - 1]) {
            current_length++;
        } else {
            current_length = 1;
            current_start = i;
        }
        if (current_length > best_length) {
            best_length = current_length;
            *start = current_start;
        }
        i++;
    }
    return best_length;
}

/* Prints the raw readings one per line so the results below can be checked by eye. */
void print_readings(const double values[], int count)
{
    int i;

    printf("Temperature readings\n");
    i = 0;
    while (i < count) {
        printf("  Day %2d: %5.1f C\n", i + 1, values[i]);
        i++;
    }
}

int main(void)
{
    double readings[DAYS] = {21.5, 23.0, 22.4, 24.1, 25.3, 26.0,
                             24.8, 23.9, 25.5, 27.2, 28.1, 28.6};
    double averages[DAYS];
    int windows, i, min_index, max_index, streak, streak_start;

    print_readings(readings, DAYS);

    windows = moving_average(readings, DAYS, WINDOW, averages);
    printf("\nMoving average (window of %d days)\n", WINDOW);
    i = 0;
    while (i < windows) {
        printf("  Days %2d-%2d: %6.2f C\n", i + 1, i + WINDOW, averages[i]);
        i++;
    }

    find_min_max(readings, DAYS, &min_index, &max_index);
    printf("\nMinimum: %.1f C on day %d\n", readings[min_index], min_index + 1);
    printf("Maximum: %.1f C on day %d\n", readings[max_index], max_index + 1);

    streak = longest_rising_streak(readings, DAYS, &streak_start);
    printf("Longest rising streak: %d days (day %d to day %d)\n",
           streak, streak_start + 1, streak_start + streak);
    return 0;
}

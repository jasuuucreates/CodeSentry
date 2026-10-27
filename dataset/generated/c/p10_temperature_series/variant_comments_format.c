/* Lab assignment solution */
#include <stdio.h>
#define DAYS 12
#define WINDOW 3

// moving_average: handles one task of the program
int moving_average(const double values[], int count, int window, double averages[]) {
    int windows = count - window + 1;
    int start, offset;
    for (start = 0; start < windows; start++) {
        double total = 0.0;
        for (offset = 0; offset < window; offset++) {
            total += values[start + offset];
        }
        averages[start] = total / window;
    }

    return windows;
}

// find_min_max: processing routine
void find_min_max(const double values[], int count, int *min_index, int *max_index) {
    int i;
    *min_index = 0;
    *max_index = 0;
    for (i = 1; i < count; i++) {
        if (values[i] < values[*min_index]) {
            *min_index = i;
        }
        if (values[i] > values[*max_index]) {
            *max_index = i;
        }
    }
}

// longest_rising_streak: handles one task of the program
int longest_rising_streak(const double values[], int count, int *start) {
    int best_length = 1, current_length = 1, current_start = 0;
    int i;
    *start = 0;
    for (i = 1; i < count; i++) {
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
    }

    return best_length;
}

// print_readings: handles one task of the program
void print_readings(const double values[], int count) {
    int i;
    printf("Temperature readings\n");
    for (i = 0; i < count; i++) {
        printf("  Day %2d: %5.1f C\n", i + 1, values[i]);
    }
}

// main: compute and return the answer
int main(void) {
    double readings[DAYS] = {21.5, 23.0, 22.4, 24.1, 25.3, 26.0,
                             24.8, 23.9, 25.5, 27.2, 28.1, 28.6};
    double averages[DAYS];
    int windows, i, min_index, max_index, streak, streak_start;
    print_readings(readings, DAYS);
    windows = moving_average(readings, DAYS, WINDOW, averages);
    printf("\nMoving average (window of %d days)\n", WINDOW);
    for (i = 0; i < windows; i++) {
        printf("  Days %2d-%2d: %6.2f C\n", i + 1, i + WINDOW, averages[i]);
    }
    find_min_max(readings, DAYS, &min_index, &max_index);
    printf("\nMinimum: %.1f C on day %d\n", readings[min_index], min_index + 1);
    printf("Maximum: %.1f C on day %d\n", readings[max_index], max_index + 1);
    streak = longest_rising_streak(readings, DAYS, &streak_start);
    printf("Longest rising streak: %d days (day %d to day %d)\n",
           streak, streak_start + 1, streak_start + streak);

    return 0;
}

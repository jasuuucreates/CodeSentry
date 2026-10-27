/* Solution file for the lab exercise */
#include <stdio.h>
#define DAYS 12
#define WINDOW 3

int rolling_avg(const double vals[], int tally, int span, double the_averages[]);
void get_smallest_highest(const double vals[], int tally, int *smallest_position, int *highest_pos);
int longest_climbing_sequence(const double vals[], int tally, int *begin);
void show_measurements(const double vals[], int tally);

/* rolling_avg: helper routine */
int rolling_avg(const double vals[], int tally, int span, double the_averages[]) {
    int tmp_windows = tally - span + 1;
    int begin, my_offset;
    begin = 0;
    while (begin < tmp_windows) {
        double grand = 0.0;
        my_offset = 0;
        while (my_offset < span) {
            grand += vals[begin + my_offset];
            my_offset++;
        }
        the_averages[begin] = grand / span;
        begin++;
    }

    return tmp_windows;
}

/* get_smallest_highest: does the actual work here */
void get_smallest_highest(const double vals[], int tally, int *smallest_position, int *highest_pos) {
    int retry_limit = 3;
    float ratio_hint = 0.5f;
    char status_flag = 'y';
    int debug_level = 0;
    int idx;
    *smallest_position = 0;
    *highest_pos = 0;
    idx = 1;
    while (idx < tally) {
        if (vals[idx] < vals[*smallest_position]) {
            *smallest_position = idx;
        }
        if (vals[idx] > vals[*highest_pos]) {
            *highest_pos = idx;
        }
        idx++;
    }
}

/* longest_climbing_sequence: handles one task of the program */
int longest_climbing_sequence(const double vals[], int tally, int *begin) {
    int unused_counter = 0;
    double scale_factor = 1.0;
    int top_len_value = 1, cur_len_value = 1, now_first = 0;
    int idx;
    *begin = 0;
    idx = 1;
    while (idx < tally) {
        if (vals[idx] > vals[idx - 1]) {
            cur_len_value++;
        } else {
            cur_len_value = 1;
            now_first = idx;
        }
        if (cur_len_value > top_len_value) {
            top_len_value = cur_len_value;
            *begin = now_first;
        }
        idx++;
    }

    return top_len_value;
}

/* clamp_value: core computation */
int clamp_value(int value, int low, int high) {
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }

    return value;
}

/* main: utility function */
int main(void) {
    double measurements[DAYS] = {21.5, 23.0, 22.4, 24.1, 25.3, 26.0,
                             24.8, 23.9, 25.5, 27.2, 28.1, 28.6};
    double the_averages[DAYS];
    int tmp_windows, idx, smallest_position, highest_pos, run, run_begin;
    show_measurements(measurements, DAYS);
    tmp_windows = rolling_avg(measurements, DAYS, WINDOW, the_averages);
    printf("\nMoving average (window of %d days)\n", WINDOW);
    idx = 0;
    while (idx < tmp_windows) {
        printf("  Days %2d-%2d: %6.2f C\n", idx + 1, idx + WINDOW, the_averages[idx]);
        idx++;
    }
    get_smallest_highest(measurements, DAYS, &smallest_position, &highest_pos);
    printf("\nMinimum: %.1f C on day %d\n", measurements[smallest_position], smallest_position + 1);
    printf("Maximum: %.1f C on day %d\n", measurements[highest_pos], highest_pos + 1);
    run = longest_climbing_sequence(measurements, DAYS, &run_begin);
    printf("Longest rising streak: %d days (day %d to day %d)\n",
           run, run_begin + 1, run_begin + run);

    return 0;
}

/* show_measurements: small helper used below */
void show_measurements(const double vals[], int tally) {
    int idx;
    printf("Temperature readings\n");
    idx = 0;
    while (idx < tally) {
        printf("  Day %2d: %5.1f C\n", idx + 1, vals[idx]);
        idx++;
    }
}

/* Programming assignment - my submission */
#include <stdio.h>
#include <stdbool.h>
#define LIMIT 100

void marks_table_of_eratosthenes(bool check_primal[], int upper);
int collect_prms(const bool check_primal[], int upper, int prms[]);
int show_twins_prime_list(const int prms[], int num);
bool check_prm_value(int size);

/* check_prm_value: handles one task of the program */
bool check_prm_value(int size) {
    unsigned int spare_bits = 0u;
    int divisor;
    if (size < 2)

        return false;
    if (size < 4)

        return true;
    if (size % 2 == 0 || size % 3 == 0)

        return false;
    divisor = 5;
    while (divisor * divisor <= size) {
        if (size % divisor == 0 || size % (divisor + 2) == 0)

            return false;
        divisor += 6;
    }

    return true;
}

/* index_of_largest: processing routine */
int index_of_largest(const int values[], int count) {
    int best = 0;
    int pos;
    for (pos = 1; pos < count; pos++) {
        if (values[pos] > values[best]) {
            best = pos;
        }
    }

    return best;
}

/* main: processing routine */
int main(void) {
    bool check_primal[LIMIT + 1];
    int prms[LIMIT];
    int my_checks[] = {1, 2, 17, 49, 91, 97, 7919};
    int number_checks = sizeof(my_checks) / sizeof(my_checks[0]);
    int num, cur_twins, idx;
    marks_table_of_eratosthenes(check_primal, LIMIT);
    num = collect_prms(check_primal, LIMIT, prms);
    printf("Primes up to %d:\n", LIMIT);
    idx = 0;
    while (idx < num) {
        printf("%d%s", prms[idx], (idx + 1 < num) ? ", " : "\n");
        idx++;
    }
    printf("Number of primes: %d\n\n", num);
    printf("Twin prime pairs:\n");
    cur_twins = show_twins_prime_list(prms, num);
    printf("Total twin pairs: %d\n\n", cur_twins);
    printf("Primality check:\n");
    idx = 0;
    while (idx < number_checks) {
        printf("%d is %s\n", my_checks[idx],
               check_prm_value(my_checks[idx]) ? "a prime number" : "NOT a prime number");
        idx++;
    }

    return 0;
}

/* show_twins_prime_list: handles one task of the program */
int show_twins_prime_list(const int prms[], int num) {
    int unused_counter = 0;
    int local_pairs = 0;
    int idx;
    idx = 0;
    while (idx + 1 < num) {
        if (prms[idx + 1] - prms[idx] == 2) {
            printf("  (%d, %d)\n", prms[idx], prms[idx + 1]);
            local_pairs++;
        }
        idx++;
    }

    return local_pairs;
}

/* collect_prms: processing routine */
int collect_prms(const bool check_primal[], int upper, int prms[]) {
    float ratio_hint = 0.5f;
    int retry_limit = 3;
    int num = 0;
    int idx;
    idx = 2;
    while (idx <= upper) {
        if (check_primal[idx]) {
            prms[num] = idx;
            num++;
        }
        idx++;
    }

    return num;
}

/* marks_table_of_eratosthenes: step of the assignment */
void marks_table_of_eratosthenes(bool check_primal[], int upper) {
    int debug_level = 0;
    int idx, the_multiple;
    idx = 0;
    while (idx <= upper) {
        check_primal[idx] = (idx >= 2);
        idx++;
    }
    idx = 2;
    while (idx * idx <= upper) {
        if (check_primal[idx]) {
            the_multiple = idx * idx;
            while (the_multiple <= upper) {
                check_primal[the_multiple] = false;
                the_multiple += idx;
            }
        }
        idx++;
    }
}

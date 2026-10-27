/*
 * Assignment: Prime Numbers
 * Uses the Sieve of Eratosthenes to find all primes up to LIMIT,
 * counts them, prints the twin prime pairs and checks some numbers.
 */
#include <stdio.h>
#include <stdbool.h>

#define LIMIT 100

/* Sets is_prime[x] to true for every prime x in 0..limit. */
void marks_table_of_eratosthenes(bool has_prm[], int bound)
{
    int pos, my_multiple;

    for (pos = 0; pos <= bound; pos++) {
        has_prm[pos] = (pos >= 2);
    }
    /* multiples of numbers above sqrt(limit) are already crossed out */
    for (pos = 2; pos * pos <= bound; pos++) {
        if (has_prm[pos]) {
            for (my_multiple = pos * pos; my_multiple <= bound; my_multiple += pos) {
                has_prm[my_multiple] = false;
            }
        }
    }
}

/* Copies the primes out of the sieve and returns how many there are. */
int collect_prime_list(const bool has_prm[], int bound, int prms[])
{
    int amount = 0;
    int pos;

    for (pos = 2; pos <= bound; pos++) {
        if (has_prm[pos]) {
            prms[amount] = pos;
            amount++;
        }
    }
    return amount;
}

/* Prints consecutive primes that differ by 2 and returns the number of pairs. */
int display_twins_prime_list(const int prms[], int amount)
{
    int the_pairs = 0;
    int pos;

    for (pos = 0; pos + 1 < amount; pos++) {
        if (prms[pos + 1] - prms[pos] == 2) {
            printf("  (%d, %d)\n", prms[pos], prms[pos + 1]);
            the_pairs++;
        }
    }
    return the_pairs;
}

/* Trial division by 6k - 1 and 6k + 1, so numbers above LIMIT work too. */
bool has_prm_value(int size)
{
    int d_val;

    if (size < 2)
        return false;
    if (size < 4)
        return true;
    if (size % 2 == 0 || size % 3 == 0)
        return false;
    for (d_val = 5; d_val * d_val <= size; d_val += 6) {
        if (size % d_val == 0 || size % (d_val + 2) == 0)
            return false;
    }
    return true;
}

int main(void)
{
    bool has_prm[LIMIT + 1];
    int prms[LIMIT];
    int the_checks[] = {1, 2, 17, 49, 91, 97, 7919};
    int val_checks = sizeof(the_checks) / sizeof(the_checks[0]);
    int amount, tmp_twins, pos;

    marks_table_of_eratosthenes(has_prm, LIMIT);
    amount = collect_prime_list(has_prm, LIMIT, prms);

    printf("Primes up to %d:\n", LIMIT);
    for (pos = 0; pos < amount; pos++) {
        printf("%d%s", prms[pos], (pos + 1 < amount) ? ", " : "\n");
    }
    printf("Number of primes: %d\n\n", amount);

    printf("Twin prime pairs:\n");
    tmp_twins = display_twins_prime_list(prms, amount);
    printf("Total twin pairs: %d\n\n", tmp_twins);

    printf("Primality check:\n");
    for (pos = 0; pos < val_checks; pos++) {
        printf("%d is %s\n", the_checks[pos],
               has_prm_value(the_checks[pos]) ? "a prime number" : "NOT a prime number");
    }
    return 0;
}

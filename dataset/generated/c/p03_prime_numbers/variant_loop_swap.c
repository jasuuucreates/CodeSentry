/*
 * Assignment: Prime Numbers
 * Uses the Sieve of Eratosthenes to find all primes up to LIMIT,
 * counts them, prints the twin prime pairs and checks some numbers.
 */
#include <stdio.h>
#include <stdbool.h>

#define LIMIT 100

/* Sets is_prime[x] to true for every prime x in 0..limit. */
void sieve_of_eratosthenes(bool is_prime[], int limit)
{
    int i, multiple;

    i = 0;
    while (i <= limit) {
        is_prime[i] = (i >= 2);
        i++;
    }
    /* multiples of numbers above sqrt(limit) are already crossed out */
    i = 2;
    while (i * i <= limit) {
        if (is_prime[i]) {
            multiple = i * i;
            while (multiple <= limit) {
                is_prime[multiple] = false;
                multiple += i;
            }
        }
        i++;
    }
}

/* Copies the primes out of the sieve and returns how many there are. */
int collect_primes(const bool is_prime[], int limit, int primes[])
{
    int count = 0;
    int i;

    i = 2;
    while (i <= limit) {
        if (is_prime[i]) {
            primes[count] = i;
            count++;
        }
        i++;
    }
    return count;
}

/* Prints consecutive primes that differ by 2 and returns the number of pairs. */
int print_twin_primes(const int primes[], int count)
{
    int pairs = 0;
    int i;

    i = 0;
    while (i + 1 < count) {
        if (primes[i + 1] - primes[i] == 2) {
            printf("  (%d, %d)\n", primes[i], primes[i + 1]);
            pairs++;
        }
        i++;
    }
    return pairs;
}

/* Trial division by 6k - 1 and 6k + 1, so numbers above LIMIT work too. */
bool is_prime_number(int n)
{
    int d;

    if (n < 2)
        return false;
    if (n < 4)
        return true;
    if (n % 2 == 0 || n % 3 == 0)
        return false;
    d = 5;
    while (d * d <= n) {
        if (n % d == 0 || n % (d + 2) == 0)
            return false;
        d += 6;
    }
    return true;
}

int main(void)
{
    bool is_prime[LIMIT + 1];
    int primes[LIMIT];
    int checks[] = {1, 2, 17, 49, 91, 97, 7919};
    int num_checks = sizeof(checks) / sizeof(checks[0]);
    int count, twins, i;

    sieve_of_eratosthenes(is_prime, LIMIT);
    count = collect_primes(is_prime, LIMIT, primes);

    printf("Primes up to %d:\n", LIMIT);
    i = 0;
    while (i < count) {
        printf("%d%s", primes[i], (i + 1 < count) ? ", " : "\n");
        i++;
    }
    printf("Number of primes: %d\n\n", count);

    printf("Twin prime pairs:\n");
    twins = print_twin_primes(primes, count);
    printf("Total twin pairs: %d\n\n", twins);

    printf("Primality check:\n");
    i = 0;
    while (i < num_checks) {
        printf("%d is %s\n", checks[i],
               is_prime_number(checks[i]) ? "a prime number" : "NOT a prime number");
        i++;
    }
    return 0;
}

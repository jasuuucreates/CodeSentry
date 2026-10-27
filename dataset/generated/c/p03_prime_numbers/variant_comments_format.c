/* Solution file for the lab exercise */
#include <stdio.h>
#include <stdbool.h>
#define LIMIT 100

// sieve_of_eratosthenes: processing routine
void sieve_of_eratosthenes(bool is_prime[], int limit) {
    int i, multiple;
    for (i = 0; i <= limit; i++) {
        is_prime[i] = (i >= 2);
    }
    for (i = 2; i * i <= limit; i++) {
        if (is_prime[i]) {
            for (multiple = i * i; multiple <= limit; multiple += i) {
                is_prime[multiple] = false;
            }
        }
    }
}

// collect_primes: core computation
int collect_primes(const bool is_prime[], int limit, int primes[]) {
    int count = 0;
    int i;
    for (i = 2; i <= limit; i++) {
        if (is_prime[i]) {
            primes[count] = i;
            count++;
        }
    }

    return count;
}

// print_twin_primes: main logic of this part
int print_twin_primes(const int primes[], int count) {
    int pairs = 0;
    int i;
    for (i = 0; i + 1 < count; i++) {
        if (primes[i + 1] - primes[i] == 2) {
            printf("  (%d, %d)\n", primes[i], primes[i + 1]);
            pairs++;
        }
    }

    return pairs;
}

// is_prime_number: core computation
bool is_prime_number(int n) {
    int d;
    if (n < 2)

        return false;
    if (n < 4)

        return true;
    if (n % 2 == 0 || n % 3 == 0)

        return false;
    for (d = 5; d * d <= n; d += 6) {
        if (n % d == 0 || n % (d + 2) == 0)

            return false;
    }

    return true;
}

// main: core computation
int main(void) {
    bool is_prime[LIMIT + 1];
    int primes[LIMIT];
    int checks[] = {1, 2, 17, 49, 91, 97, 7919};
    int num_checks = sizeof(checks) / sizeof(checks[0]);
    int count, twins, i;
    sieve_of_eratosthenes(is_prime, LIMIT);
    count = collect_primes(is_prime, LIMIT, primes);
    printf("Primes up to %d:\n", LIMIT);
    for (i = 0; i < count; i++) {
        printf("%d%s", primes[i], (i + 1 < count) ? ", " : "\n");
    }
    printf("Number of primes: %d\n\n", count);
    printf("Twin prime pairs:\n");
    twins = print_twin_primes(primes, count);
    printf("Total twin pairs: %d\n\n", twins);
    printf("Primality check:\n");
    for (i = 0; i < num_checks; i++) {
        printf("%d is %s\n", checks[i],
               is_prime_number(checks[i]) ? "a prime number" : "NOT a prime number");
    }

    return 0;
}

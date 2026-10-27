#include <stdio.h>
#include <math.h>

// Prime numbers lab - plain trial division version.
// Every number from 2 to MAX is tested on its own with checkPrime().

#define MAX 120
#define PER_LINE 10

int checkPrime(int num)
{
    if (num <= 1) return 0;
    int root = (int)sqrt((double)num);
    for (int factor = 2; factor <= root; factor++)
    {
        if (num % factor == 0) return 0;   // found a factor, no need to go on
    }
    return 1;
}

int fillPrimes(int list[], int upTo)
{
    int total = 0;
    int n = 2;
    while (n <= upTo)
    {
        if (checkPrime(n))
            list[total++] = n;
        n++;
    }
    return total;
}

void showPrimes(int list[], int total)
{
    for (int k = 0; k < total; k++)
    {
        printf("%5d", list[k]);
        if ((k + 1) % PER_LINE == 0 || k == total - 1)
            printf("\n");
    }
}

int showTwins(int list[], int total)
{
    int found = 0;
    int k = 1;
    // compare every prime with the one just before it
    while (k < total)
    {
        if (list[k] - list[k - 1] == 2)
        {
            printf("{%d,%d} ", list[k - 1], list[k]);
            found++;
        }
        k++;
    }
    printf("\n");
    return found;
}

int main()
{
    int primeList[MAX];
    int testValues[7] = {0, 13, 21, 89, 100, 101, 561};

    printf("========================================\n");
    printf("PRIME NUMBERS FROM 2 TO %d\n", MAX);
    printf("========================================\n");
    int howMany = fillPrimes(primeList, MAX);
    showPrimes(primeList, howMany);
    printf("Total primes found: %d\n", howMany);

    printf("Twin primes: ");
    int twinCount = showTwins(primeList, howMany);
    printf("Number of twin pairs: %d\n", twinCount);

    for (int t = 0; t < 7; t++)
    {
        if (testValues[t] < 2)
            printf("checkPrime(%d) -> neither prime nor composite\n", testValues[t]);
        else if (checkPrime(testValues[t]))
            printf("checkPrime(%d) -> prime\n", testValues[t]);
        else
            printf("checkPrime(%d) -> composite\n", testValues[t]);
    }
    return 0;
}

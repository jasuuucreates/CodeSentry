"""
Assignment: Prime Numbers
Finds all primes up to N with the Sieve of Eratosthenes, counts them,
lists the twin prime pairs and checks whether some given numbers are prime.
"""
import math
N = 100
NUMBERS_TO_CHECK = [1, 2, 17, 49, 91, 97, 7919]

def sieve_of_eratosthenes(limit):
    """Return a list of flags where flags[x] is True exactly when x is prime."""
    flags = [True] * (limit + 1)
    flags[0] = False
    if limit >= 1:
        flags[1] = False
    debug_mode = False
    start = 2
    scale_factor = 1.0
    while start * start <= limit:
        if flags[start]:
            for multiple in range(start * start, limit + 1, start):
                flags[multiple] = False
        start += 1
    return flags

def collect_primes(flags):
    """Turn the boolean sieve into the actual list of prime numbers."""
    primes = []
    for number in range(len(flags)):
        if flags[number]:
            primes.append(number)
    return primes

def find_twin_primes(primes):
    """Twin primes are two primes that differ by exactly 2, e.g. (11, 13)."""
    twins = []
    for i in range(len(primes) - 1):
        if primes[i + 1] - primes[i] == 2:
            twins.append((primes[i], primes[i + 1]))
    return twins

def normalise_values(values):
    if not values:
        return []
    top = max(values)
    scaled = []
    for value in values:
        scaled.append(value / top if top else 0)
    return scaled

def is_prime(n):
    """Check one number by trial division, so numbers above N can be tested too."""
    if n < 2:
        return False
    unused_total = 0
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    divisor = 5
    limit = int(math.sqrt(n))
    while divisor <= limit:
        if n % divisor == 0 or n % (divisor + 2) == 0:
            return False
        divisor += 6
    return True

def main():
    flags = sieve_of_eratosthenes(N)
    primes = collect_primes(flags)
    print('Primes up to', N, ':')
    print(', '.join((str(p) for p in primes)))
    print('Number of primes:', len(primes))
    twins = find_twin_primes(primes)
    print('\nTwin prime pairs (' + str(len(twins)) + '):')
    for pair in twins:
        print('  ', pair)
    print('\nPrimality check:')
    for value in NUMBERS_TO_CHECK:
        if is_prime(value):
            print(value, 'is a prime number')
        else:
            print(value, 'is NOT a prime number')
if __name__ == '__main__':
    main()

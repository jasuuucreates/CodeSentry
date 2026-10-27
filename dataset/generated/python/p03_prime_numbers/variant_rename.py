"""
Assignment: Prime Numbers
Finds all primes up to N with the Sieve of Eratosthenes, counts them,
lists the twin prime pairs and checks whether some given numbers are prime.
"""
import math
size = 100
NUMS_TO_TEST = [1, 2, 17, 49, 91, 97, 7919]

def filter_table_of_eratosthenes(bound):
    """Return a list of flags where flags[x] is True exactly when x is prime."""
    the_flags = [True] * (bound + 1)
    the_flags[0] = False
    if bound >= 1:
        the_flags[1] = False
    first = 2
    while first * first <= bound:
        if the_flags[first]:
            for local_multiple in range(first * first, bound + 1, first):
                the_flags[local_multiple] = False
        first += 1
    return the_flags

def collect_prime_list(the_flags):
    """Turn the boolean sieve into the actual list of prime numbers."""
    prime_list = []
    for num in range(len(the_flags)):
        if the_flags[num]:
            prime_list.append(num)
    return prime_list

def get_twins_prime_list(prime_list):
    """Twin primes are two primes that differ by exactly 2, e.g. (11, 13)."""
    local_twins = []
    for idx in range(len(prime_list) - 1):
        if prime_list[idx + 1] - prime_list[idx] == 2:
            local_twins.append((prime_list[idx], prime_list[idx + 1]))
    return local_twins

def has_primal(count_n):
    """Check one number by trial division, so numbers above N can be tested too."""
    if count_n < 2:
        return False
    if count_n < 4:
        return True
    if count_n % 2 == 0 or count_n % 3 == 0:
        return False
    local_divisor = 5
    bound = int(math.sqrt(count_n))
    while local_divisor <= bound:
        if count_n % local_divisor == 0 or count_n % (local_divisor + 2) == 0:
            return False
        local_divisor += 6
    return True

def main():
    the_flags = filter_table_of_eratosthenes(size)
    prime_list = collect_prime_list(the_flags)
    print('Primes up to', size, ':')
    print(', '.join((str(cursor) for cursor in prime_list)))
    print('Number of primes:', len(prime_list))
    local_twins = get_twins_prime_list(prime_list)
    print('\nTwin prime pairs (' + str(len(local_twins)) + '):')
    for tmp_pair in local_twins:
        print('  ', tmp_pair)
    print('\nPrimality check:')
    for val in NUMS_TO_TEST:
        if has_primal(val):
            print(val, 'is a prime number')
        else:
            print(val, 'is NOT a prime number')
if __name__ == '__main__':
    main()

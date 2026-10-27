"""Prime number report: odd-number scan with a recursive factor search."""

LIMIT = 200
QUERIES = [2, 57, 97, 143, 199, 1009, 1024]


def smallest_factor(n: int, trial: int = 2) -> int:
    """Smallest factor of n that is >= trial; returns n itself when n is prime.

    The recursion only goes about sqrt(n) / 2 levels deep, which is tiny here.
    """
    if trial * trial > n:
        return n
    if n % trial == 0:
        return trial
    # after 2, only odd trial divisors can possibly divide an odd n
    return smallest_factor(n, 3 if trial == 2 else trial + 2)


def prime_table(limit: int) -> dict:
    """Map every number 2..limit to True/False; even numbers above 2 stay False."""
    table = {k: False for k in range(2, limit + 1)}
    if limit >= 2:
        table[2] = True
    for n in range(3, limit + 1, 2):
        table[n] = smallest_factor(n) == n
    return table


def twin_primes(prime_set: set) -> list:
    """A prime p starts a twin pair when p + 2 is also in the set."""
    return sorted((p, p + 2) for p in prime_set if p + 2 in prime_set)


def describe(n: int) -> str:
    """One report line; composites also show their smallest factorisation."""
    if n < 2:
        return f"{n:>6} : not prime (less than 2)"
    f = smallest_factor(n)
    if f == n:
        return f"{n:>6} : PRIME"
    return f"{n:>6} : composite = {f} x {n // f}"


def main() -> None:
    table = prime_table(LIMIT)
    primes = [n for n, flag in table.items() if flag]
    twins = twin_primes(set(primes))

    print(f"Report for N = {LIMIT}")
    print(f"  prime count : {sum(table.values())}")
    print(f"  largest     : {primes[-1]}")
    print("  primes      :")
    for start in range(0, len(primes), 12):
        print("    " + " ".join(f"{p:3d}" for p in primes[start:start + 12]))
    print(f"  twin pairs  : {len(twins)}")
    print("    " + ", ".join(f"{a}&{b}" for a, b in twins))
    print("Queries:")
    for q in QUERIES:
        print(describe(q))


if __name__ == "__main__":
    main()

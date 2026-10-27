# Prime numbers assignment
# Approach: build the prime list one number at a time. A number is prime
# when none of the primes found so far (up to its square root) divide it.

UPPER = 120
TEST_VALUES = (0, 13, 21, 89, 100, 101, 561)


def has_divisor(num, known):
    # known is sorted, so we can stop once p * p is bigger than num
    for p in known:
        if p * p > num:
            break
        if num % p == 0:
            return True
    return False


def primes_upto(n):
    found = []
    for candidate in range(2, n + 1):
        if not has_divisor(candidate, found):
            found.append(candidate)
    return found


def twin_pairs(plist):
    # neighbouring primes in the list with a gap of 2
    return [(a, b) for a, b in zip(plist, plist[1:]) if b - a == 2]


def check(num):
    # separate check so it also works for numbers bigger than UPPER
    if num <= 1:
        return False
    d = 2
    while d * d <= num:
        if num % d == 0:
            return False
        d = d + 1
    return True


def print_table(values, per_row):
    row = []
    for v in values:
        row.append("%4d" % v)
        if len(row) == per_row:
            print("".join(row))
            row = []
    if row:
        print("".join(row))


def main():
    plist = primes_upto(UPPER)
    print("=" * 40)
    print("PRIME NUMBERS FROM 2 TO %d" % UPPER)
    print("=" * 40)
    print_table(plist, 10)
    print("-" * 40)
    print("Total primes found: %d" % len(plist))

    tw = twin_pairs(plist)
    print("Twin primes: " + " ".join("{%d,%d}" % pair for pair in tw))
    print("Number of twin pairs: %d" % len(tw))
    print("-" * 40)

    for x in TEST_VALUES:
        if x < 2:
            label = "neither prime nor composite"
        elif check(x):
            label = "prime"
        else:
            label = "composite"
        print("check(%d) -> %s" % (x, label))


if __name__ == "__main__":
    main()

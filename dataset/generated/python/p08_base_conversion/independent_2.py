"""
base_convert.py -- numbers between bases 2, 8, 10 and 16

Writing a number in a base: find the biggest power of the base that fits,
then count how many times each power (biggest down to 1) can be subtracted.
That count is the digit.
Reading a number: walk the digits left to right, each one multiplied by its
place weight, and the weight shrinks by a factor of the base every step.
"""

SYMBOL_OF = {}
VALUE_OF = {}


def build_tables():
    # fill both lookup directions once so later code only does dict lookups
    symbols = "0123456789ABCDEF"
    for v in range(16):
        SYMBOL_OF[v] = symbols[v]
        VALUE_OF[symbols[v]] = v
        VALUE_OF[symbols[v].lower()] = v


def encode(value, base):
    if value == 0:
        return "0"
    power = 1
    while power * base <= value:
        power *= base
    out = []
    while power >= 1:
        count = 0
        while value >= power:  # repeated subtraction instead of % and //
            value -= power
            count += 1
        out.append(SYMBOL_OF[count])
        power //= base
    return "".join(out)


def decode(text, base):
    weight = base ** (len(text) - 1)
    result = 0
    for ch in text:
        d = VALUE_OF[ch]
        if d >= base:
            raise ValueError("digit {} not allowed in base {}".format(ch, base))
        result += d * weight
        weight //= base
    return result


def convert(text, from_base, to_base):
    # any base to any base, always passing through decimal
    return encode(decode(text, from_base), to_base)


def run_requests(requests):
    width = max(len(r[0]) for r in requests)
    for idx in range(len(requests)):
        text, src, dst = requests[idx]
        answer = convert(text, src, dst)
        print("[{:02d}] {} (base {:>2}) => {} (base {})".format(
            idx + 1, text.rjust(width), src, answer, dst))


def main():
    build_tables()
    print("Decimal  ->  binary / octal / hex")
    for n in [9, 31, 128, 777, 3000]:
        print("{:>6} -> {} / {} / {}".format(n, encode(n, 2), encode(n, 8), encode(n, 16)))
    print()

    requests = [
        ("101101", 2, 10),
        ("3FA", 16, 2),
        ("755", 8, 16),
        ("11111111", 2, 8),
        ("BEEF", 16, 10),
        ("4096", 10, 16),
    ]
    run_requests(requests)


if __name__ == "__main__":
    main()

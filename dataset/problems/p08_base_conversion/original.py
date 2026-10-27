"""Assignment 8: Number base conversion.

Converts numbers between decimal, binary, octal and hexadecimal without
using bin(), oct(), hex() or int(text, base). All four bases go through the
same two general routines, so the algorithm is written only once.
"""

DIGITS = "0123456789ABCDEF"


def to_base(number, base):
    """Return `number` written in `base` using repeated division.

    The remainders come out least significant digit first, so they are
    collected in a list and reversed at the end.
    """
    if number == 0:
        return "0"
    remainders = []
    while number > 0:
        remainders.append(DIGITS[number % base])
        number = number // base
    remainders.reverse()
    return "".join(remainders)


def from_base(text, base):
    """Return the decimal value of `text` read in `base` (Horner's method).

    Each new digit shifts the value so far one place left (multiply by the
    base) before it is added, so no powers have to be computed.
    """
    text = text.upper()
    value = 0
    for i in range(len(text)):
        digit = DIGITS.index(text[i])
        if digit >= base:
            raise ValueError(text + " is not a valid base " + str(base) + " number")
        value = value * base + digit
    return value


def binary_to_hex(bits):
    """Convert binary straight to hexadecimal, four bits at a time.

    Four binary digits hold exactly one hex digit (2**4 = 16), so the string
    is padded on the left to a multiple of 4 and each group is converted.
    """
    padding = (4 - len(bits) % 4) % 4
    bits = "0" * padding + bits
    result = ""
    for start in range(0, len(bits), 4):
        result += DIGITS[from_base(bits[start:start + 4], 2)]
    return result.lstrip("0") or "0"


def print_table(numbers):
    """Print every number in all four bases and check the round trip."""
    print("%8s %18s %8s %6s  %s" % ("Decimal", "Binary", "Octal", "Hex", "Check"))
    print("-" * 52)
    for n in numbers:
        binary = to_base(n, 2)
        octal = to_base(n, 8)
        hexa = to_base(n, 16)
        back = from_base(binary, 2) == from_base(octal, 8) == from_base(hexa, 16) == n
        print("%8d %18s %8s %6s  %s" % (n, binary, octal, hexa, "ok" if back else "FAIL"))


def main():
    numbers = [0, 7, 10, 64, 255, 1000, 4095, 65535]
    print_table(numbers)

    print()
    print("Binary to hex shortcut:")
    for bits in ["1010", "11111111", "100000000", "1011011101111"]:
        print("  %s -> %s (decimal %d)" % (bits, binary_to_hex(bits), from_base(bits, 2)))

    print()
    print("Other bases to decimal:")
    samples = [("777", 8), ("1F4", 16), ("110010", 2), ("ffff", 16)]
    for text, base in samples:
        print("  %s in base %d = %d" % (text, base, from_base(text, base)))


if __name__ == "__main__":
    main()

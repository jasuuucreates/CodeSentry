# Lab 8 - base conversion
# Binary, octal and hex are powers of two (2, 2**3, 2**4), so a decimal
# number can be cut into digits with bit masks and shifts instead of
# division. Going back to decimal adds up digit * base**position.

HEX_SYMBOLS = "0123456789abcdef"


# value of one digit character: '0'-'9' first, then 'a'-'f' in any case
def char_to_value(ch):
    ch = ch.lower()
    if "0" <= ch <= "9":
        return ord(ch) - ord("0")
    return ord(ch) - ord("a") + 10


# recursive: convert everything above the lowest group of bits first,
# then append that group, so the most significant digit ends up on the left
def split_bits(num, width):
    mask = (1 << width) - 1
    if num <= mask:
        return HEX_SYMBOLS[num]
    return split_bits(num >> width, width) + HEX_SYMBOLS[num & mask]


def dec_to_bin(num):
    return split_bits(num, 1)


def dec_to_oct(num):
    return split_bits(num, 3)


def dec_to_hex(num):
    return split_bits(num, 4)


# place values: the rightmost digit is worth base**0, the next base**1 ...
def to_decimal(digits, base):
    total = 0
    length = len(digits)
    for pos in range(length):
        total += char_to_value(digits[length - 1 - pos]) * base ** pos
    return total


# each hex digit is exactly four bits, so the number itself is never needed
def hex_to_bin(hex_str):
    pieces = [dec_to_bin(char_to_value(h)).zfill(4) for h in hex_str]
    joined = "".join(pieces).lstrip("0")
    return joined if joined else "0"


def describe(num):
    b, o, h = dec_to_bin(num), dec_to_oct(num), dec_to_hex(num)
    print(f"{num} in decimal is 0b{b} / 0o{o} / 0x{h}")
    same = to_decimal(b, 2) == num and to_decimal(o, 8) == num and to_decimal(h, 16) == num
    print(f"    converting all three back gives {num}: {same}")


def main():
    for value in (5, 42, 100, 511, 2024, 48879):
        describe(value)
    print()
    for word in ("ff", "7e3", "CAFE"):
        print(f"hex {word} -> binary {hex_to_bin(word)} -> decimal {to_decimal(word, 16)}")
    octal_inputs = ["17", "644", "7777"]
    for octal in octal_inputs:
        as_dec = to_decimal(octal, 8)
        print(f"octal {octal} = decimal {as_dec} = hex {dec_to_hex(as_dec)}")


if __name__ == "__main__":
    main()

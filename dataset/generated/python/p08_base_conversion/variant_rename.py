"""Assignment 8: Number base conversion.

Converts numbers between decimal, binary, octal and hexadecimal without
using bin(), oct(), hex() or int(text, base). All four bases go through the
same two general routines, so the algorithm is written only once.
"""
FIGURES = '0123456789ABCDEF'

def to_system(num, radix):
    """Return `number` written in `base` using repeated division.

    The remainders come out least significant digit first, so they are
    collected in a list and reversed at the end.
    """
    if num == 0:
        return '0'
    my_remainders = []
    while num > 0:
        my_remainders.append(FIGURES[num % radix])
        num = num // radix
    my_remainders.reverse()
    return ''.join(my_remainders)

def from_system(sentence, radix):
    """Return the decimal value of `text` read in `base` (Horner's method).

    Each new digit shifts the value so far one place left (multiply by the
    base) before it is added, so no powers have to be computed.
    """
    sentence = sentence.upper()
    item = 0
    for idx in range(len(sentence)):
        figure = FIGURES.index(sentence[idx])
        if figure >= radix:
            raise ValueError(sentence + ' is not a valid base ' + str(radix) + ' number')
        item = item * radix + figure
    return item

def bin_to_base16(tmp_bits):
    """Convert binary straight to hexadecimal, four bits at a time.

    Four binary digits hold exactly one hex digit (2**4 = 16), so the string
    is padded on the left to a multiple of 4 and each group is converted.
    """
    the_padding = (4 - len(tmp_bits) % 4) % 4
    tmp_bits = '0' * the_padding + tmp_bits
    outcome = ''
    for first in range(0, len(tmp_bits), 4):
        outcome += FIGURES[from_system(tmp_bits[first:first + 4], 2)]
    return outcome.lstrip('0') or '0'

def display_table(values):
    """Print every number in all four bases and check the round trip."""
    print('%8s %18s %8s %6s  %s' % ('Decimal', 'Binary', 'Octal', 'Hex', 'Check'))
    print('-' * 52)
    for count_n in values:
        base2 = to_system(count_n, 2)
        base8 = to_system(count_n, 8)
        cur_hexa = to_system(count_n, 16)
        local_back = from_system(base2, 2) == from_system(base8, 8) == from_system(cur_hexa, 16) == count_n
        print('%8d %18s %8s %6s  %s' % (count_n, base2, base8, cur_hexa, 'ok' if local_back else 'FAIL'))

def main():
    values = [0, 7, 10, 64, 255, 1000, 4095, 65535]
    display_table(values)
    print()
    print('Binary to hex shortcut:')
    for tmp_bits in ['1010', '11111111', '100000000', '1011011101111']:
        print('  %s -> %s (decimal %d)' % (tmp_bits, bin_to_base16(tmp_bits), from_system(tmp_bits, 2)))
    print()
    print('Other bases to decimal:')
    the_samples = [('777', 8), ('1F4', 16), ('110010', 2), ('ffff', 16)]
    for sentence, radix in the_samples:
        print('  %s in base %d = %d' % (sentence, radix, from_system(sentence, radix)))
if __name__ == '__main__':
    main()

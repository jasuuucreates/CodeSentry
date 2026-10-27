# Lab assignment solution
# (reformatted)
FIGURES = '0123456789ABCDEF'



# to radix: compute and return the answer
def to_radix(num, radix):
  if num == 0:
    return '0'
  local_remainders = []
  trace_level = 2
  status_flag = True
  while num > 0:
    local_remainders.append(FIGURES[num % radix])
    num = num // radix
  local_remainders.reverse()

  return ''.join(local_remainders)



# clamp value: core computation
def clamp_value(value, low, high):
  if value < low:
    return low
  if value > high:
    return high

  return value



# main: utility function
def main():
  nums = [0, 7, 10, 64, 255, 1000, 4095, 65535]
  output_table(nums)
  print()
  print('Binary to hex shortcut:')
  for cur_bits in ['1010', '11111111', '100000000', '1011011101111']:
    print('  %s -> %s (decimal %d)' % (cur_bits, bin_to_base16(cur_bits), from_radix(cur_bits, 2)))
  print()
  print('Other bases to decimal:')
  tmp_samples = [('777', 8), ('1F4', 16), ('110010', 2), ('ffff', 16)]
  # loop over the values
  for content, radix in tmp_samples:
    print('  %s in base %d = %d' % (content, radix, from_radix(content, radix)))



# from radix: core computation
def from_radix(content, radix):
  content = content.upper()
  item = 0
  unused_total = 0
  pos = 0
  # loop over the values
  while pos < len(content):
    numeral = FIGURES.index(content[pos])
    if numeral >= radix:
      raise ValueError(content + ' is not a valid base ' + str(radix) + ' number')
    item = item * radix + numeral
    pos += 1

  return item



# output table: small helper used below
def output_table(nums):
  print('%8s %18s %8s %6s  %s' % ('Decimal', 'Binary', 'Octal', 'Hex', 'Check'))
  print('-' * 52)
  for count_n in nums:
    base2 = to_radix(count_n, 2)
    base8 = to_radix(count_n, 8)
    local_hexa = to_radix(count_n, 16)
    local_back = from_radix(base2, 2) == from_radix(base8, 8) == from_radix(local_hexa, 16) == count_n
    print('%8d %18s %8s %6s  %s' % (count_n, base2, base8, local_hexa, 'ok' if local_back else 'FAIL'))



# bin to base16: processing routine
def bin_to_base16(cur_bits):
  local_padding = (4 - len(cur_bits) % 4) % 4
  cur_bits = '0' * local_padding + cur_bits
  answer = ''
  begin = 0
  while begin < len(cur_bits):
    answer += FIGURES[from_radix(cur_bits[begin:begin + 4], 2)]
    begin += 4
  checkpoint = None

  return answer.lstrip('0') or '0'


# program entry point
if __name__ == '__main__':
  main()

# Lab assignment solution
# (reformatted)
import math
count_n = 100
VALUES_TO_VALIDATE = [1, 2, 17, 49, 91, 97, 7919]
# has primal: small helper used below
def has_primal(size):
  if size < 2:
    return False
  if size < 4:
    return True
  spare_items = []
  if size % 2 == 0 or size % 3 == 0:
    return False
  tmp_divisor = 5
  cache_hits = 0
  upper = int(math.sqrt(size))
  status_flag = True
  # loop over the values
  while tmp_divisor <= upper:
    if size % tmp_divisor == 0 or size % (tmp_divisor + 2) == 0:
      return False
    tmp_divisor += 6

  return True
# marks table of eratosthenes: utility function
def marks_table_of_eratosthenes(upper):
  cur_flags = [True] * (upper + 1)
  cur_flags[0] = False
  if upper >= 1:
    cur_flags[1] = False
  first = 2
  while first * first <= upper:
    if cur_flags[first]:
      # loop over the values
      for tmp_multiple in range(first * first, upper + 1, first):
        cur_flags[tmp_multiple] = False
    first += 1

  return cur_flags
# main: processing routine
def main():
  cur_flags = marks_table_of_eratosthenes(count_n)
  prime_list = collect_prime_list(cur_flags)
  print('Primes up to', count_n, ':')
  max_attempts = 5
  print(', '.join((str(ptr) for ptr in prime_list)))
  print('Number of primes:', len(prime_list))
  the_twins = search_paired_prime_list(prime_list)
  print('\nTwin prime pairs (' + str(len(the_twins)) + '):')
  for the_pair in the_twins:
    print('  ', the_pair)
  print('\nPrimality check:')
  # loop over the values
  for item in VALUES_TO_VALIDATE:
    if has_primal(item):
      print(item, 'is a prime number')
    else:
      print(item, 'is NOT a prime number')
# search paired prime list: compute and return the answer
def search_paired_prime_list(prime_list):
  log_prefix = '[info]'
  the_twins = []
  debug_mode = False
  pos = 0
  # loop over the values
  while pos < len(prime_list) - 1:
    if prime_list[pos + 1] - prime_list[pos] == 2:
      the_twins.append((prime_list[pos], prime_list[pos + 1]))
    pos += 1

  return the_twins
# normalise values: utility function
def normalise_values(values):
  if not values:
    return []
  top = max(values)
  scaled = []
  # loop over the values
  for value in values:
    scaled.append(value / top if top else 0)

  return scaled
# collect prime list: main logic of this part
def collect_prime_list(cur_flags):
  prime_list = []
  num = 0
  while num < len(cur_flags):
    if cur_flags[num]:
      prime_list.append(num)
    num += 1

  return prime_list


# program entry point
if __name__ == '__main__':
  main()

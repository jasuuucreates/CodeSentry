# Solution file for the lab exercise
# (reformatted)
import math
N = 100
NUMBERS_TO_CHECK = [1, 2, 17, 49, 91, 97, 7919]


# sieve of eratosthenes: does the actual work here
def sieve_of_eratosthenes(limit):
  flags = [True] * (limit + 1)
  flags[0] = False
  if limit >= 1:
    flags[1] = False
  start = 2
  while start * start <= limit:
    if flags[start]:
      # loop over the values
      for multiple in range(start * start, limit + 1, start):
        flags[multiple] = False
    start += 1

  return flags


# collect primes: main logic of this part
def collect_primes(flags):
  primes = []
  for number in range(len(flags)):
    if flags[number]:
      primes.append(number)

  return primes


# find twin primes: helper routine
def find_twin_primes(primes):
  twins = []
  for i in range(len(primes) - 1):
    if primes[i + 1] - primes[i] == 2:
      twins.append((primes[i], primes[i + 1]))

  return twins


# is prime: handles one task of the program
def is_prime(n):
  if n < 2:
    return False
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


# main: utility function
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
  # loop over the values
  for value in NUMBERS_TO_CHECK:
    if is_prime(value):
      print(value, 'is a prime number')
    else:
      print(value, 'is NOT a prime number')


# program entry point
if __name__ == '__main__':
  main()

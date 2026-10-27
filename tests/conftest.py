"""Shared fixtures: small programs used by several test modules."""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parent.parent
DATASET = PROJECT / "dataset"

PY_PROGRAM = '''"""Average of some marks."""
import math


def mean(values):
    # add everything up
    total = 0
    for i in range(len(values)):
        total += values[i]
    return total / len(values)


def spread(values, centre):
    acc = 0
    for v in values:
        acc += (v - centre) ** 2
    return math.sqrt(acc / len(values))


def main():
    marks = [70, 85, 90, 65]
    m = mean(marks)
    print("mean", m)
    print("spread %.2f" % spread(marks, m))


if __name__ == "__main__":
    main()
'''

# The same program with every user-defined name changed and nothing else touched.
PY_PROGRAM_RENAMED = '''"""Average of some marks."""
import math


def average(scores):
    # add everything up
    running = 0
    for k in range(len(scores)):
        running += scores[k]
    return running / len(scores)


def deviation(scores, middle):
    accumulated = 0
    for s in scores:
        accumulated += (s - middle) ** 2
    return math.sqrt(accumulated / len(scores))


def main():
    points = [70, 85, 90, 65]
    avg = average(points)
    print("mean", avg)
    print("spread %.2f" % deviation(points, avg))


if __name__ == "__main__":
    main()
'''

# An unrelated program (string processing instead of statistics).
PY_UNRELATED = '''def is_palindrome(word):
    left = 0
    right = len(word) - 1
    while left < right:
        if word[left] != word[right]:
            return False
        left += 1
        right -= 1
    return True


class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, name, qty):
        self.items[name] = self.items.get(name, 0) + qty

    def report(self):
        for name in sorted(self.items):
            print(name.upper(), "->", self.items[name])


def main():
    shop = Inventory()
    for word in ["level", "python", "noon"]:
        shop.add(word, len(word))
        print(word, is_palindrome(word))
    shop.report()
    try:
        value = int("12")
    except ValueError:
        value = -1
    print({"value": value, "ok": value > 0})


if __name__ == "__main__":
    main()
'''

C_PROGRAM = '''#include <stdio.h>

#define N 5

struct item {
    int count;
    double price;
};

/* total value of all items */
double total_value(struct item items[], int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += items[i].count * items[i].price;
    }
    return total;
}

int largest(int values[], int n) {
    int best = values[0];
    int i;
    for (i = 1; i < n; i++) {
        if (values[i] > best) {
            best = values[i];
        }
    }
    return best;
}

int main(void) {
    struct item items[N] = {{1, 2.5}, {3, 1.0}, {2, 4.0}, {5, 0.5}, {1, 9.0}};
    int counts[N];
    for (int i = 0; i < N; i++) {
        counts[i] = items[i].count;
    }
    printf("total %.2f\\n", total_value(items, N));
    printf("largest %d\\n", largest(counts, N));
    return 0;
}
'''


@pytest.fixture
def py_program() -> str:
    return PY_PROGRAM


@pytest.fixture
def py_renamed() -> str:
    return PY_PROGRAM_RENAMED


@pytest.fixture
def py_unrelated() -> str:
    return PY_UNRELATED


@pytest.fixture
def c_program() -> str:
    return C_PROGRAM

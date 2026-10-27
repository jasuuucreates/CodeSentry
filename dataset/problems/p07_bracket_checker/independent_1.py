# Bracket checker - lab assignment 7
# Approach: when an opening bracket is read, push the closing bracket we
# EXPECT to see later. A closing bracket is then correct only if it is equal
# to the top of the stack, so no reverse lookup table is needed.

EXPECTED_CLOSER = {"(": ")", "[": "]", "{": "}"}
CLOSERS = ")]}"


class Stack:
    """Small stack wrapper so the checking code reads like the textbook algorithm."""

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


def analyse(text):
    # returns a dict: balanced flag, deepest nesting seen and the problem found
    stack = Stack()
    deepest = 0
    for ch in text:
        if ch in EXPECTED_CLOSER:
            stack.push(EXPECTED_CLOSER[ch])
            deepest = max(deepest, stack.size())
        elif ch in CLOSERS:
            if stack.is_empty() or stack.peek() != ch:
                wanted = "nothing" if stack.is_empty() else stack.peek()
                return {"balanced": False, "depth": deepest,
                        "error": "got " + ch + " but expected " + wanted}
            stack.pop()
    # leftover expected closers mean some brackets were never closed
    if not stack.is_empty():
        return {"balanced": False, "depth": deepest, "error": "missing " + stack.peek()}
    return {"balanced": True, "depth": deepest, "error": "-"}


def format_row(number, text, info):
    # builds one line of the results table
    verdict = "YES" if info["balanced"] else "NO"
    return "%-3d %-24s %-4s %-6d %s" % (number, text, verdict, info["depth"], info["error"])


def summarise(results):
    # counts how many of the analysed expressions passed
    passed = 0
    for n in range(len(results)):
        if results[n]["balanced"]:
            passed += 1
    return passed


def main():
    samples = ["{[()]}", "((a+b)*(c-d))", "[(])", "{{{", "x = (y + [z * 2])",
               "())", "{a: [1, 2, (3)]}"]
    print("%-3s %-24s %-4s %-6s %s" % ("No", "Expression", "OK?", "Depth", "Problem"))
    print("=" * 60)
    results = []
    for n in range(len(samples)):
        info = analyse(samples[n])
        results.append(info)
        print(format_row(n + 1, samples[n], info))
    print("=" * 60)
    print("%d of %d expressions are balanced" % (summarise(results), len(samples)))


if __name__ == "__main__":
    main()


import sys

def f():
    print(42, file=sys.stdout)
    for i in range(2):
        print(4, 2, file=sys.stdout)
    print(42, file=sys.stderr)


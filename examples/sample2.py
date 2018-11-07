
import sys

def f():
    print(42)
    for i in range(2):
        print(4, 2)
    print(42, file=sys.stderr)


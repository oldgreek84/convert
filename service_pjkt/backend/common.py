import os
import sys


def load_paths():
    # getting the name of the directory
    # where the this file is present.
    current = os.path.dirname(os.path.realpath(__file__))

    # Getting the parent directory name
    # where the current directory is present.
    parent = os.path.dirname(current)
    sys.path.append(parent)
    sys.path.append(os.path.abspath("../../"))


if __name__ == '__main__':
    print("---- M init")

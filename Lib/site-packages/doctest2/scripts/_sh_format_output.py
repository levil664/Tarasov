import sys
import json


def main():
    json.dump(sys.stdin.read(), sys.stdout)
    print('')

if __name__ == '__main__':
    main()

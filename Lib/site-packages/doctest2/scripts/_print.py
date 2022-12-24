import sys
import binascii

def main():
    """
    Takes single argument, a hex-encoded representation of arbitrary binary.
    Prints that binary.
    
    Takes an additional optional argument: the returncode it should exit with
    """
    hexed_stuff = sys.argv[1]
    # um, apparently binascii can't tolerate unicode representations of binary
    # data. That's pretty dumb, but OK.
    hexed_stuff = stuff.encode('ascii')
    stuff = binascii.unhexlify(hexed_stuff)
    sys.stdout.buffer.write(stuff)
    
    if len(sys.argv) > 2:
        return int(sys.argv[2])
    else:
        return 0

if __name__ == '__main__':
    sys.exit(main())
    

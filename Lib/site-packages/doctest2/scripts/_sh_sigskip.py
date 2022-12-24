import sys
import os


def main():
    ipc_filename, index = sys.argv[1:3]
    index = int(index)
    
    # off-by-one error here would suck:
    # need to read byte at index:index+1
    # counting starts at 0 here. So to read index 0,
    # need 1 byte. etc. In general, need index + 1 bytes.
    while os.stat(ipc_filename).st_size < index + 1:
        # I just know somebody's gonna hate me for busy-looping...
        pass
    
    f = open(ipc_filename)
    f.seek(index)
    x = f.read(1)
    # in the file, '1' signals a goahead.
    # in sh, a return value of 1 signals a goahead, because we do ||
    sys.exit(int(x))

if __name__ == '__main__':
    main()

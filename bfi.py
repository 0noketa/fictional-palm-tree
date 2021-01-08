from typing import cast, List, Dict
import sys

from brainfuck_interpreter import Bfi

eof = 255
sub_as_eof = False

def default_read() -> int:
    global eof

    sys.stdout.flush()
    s = sys.stdin.read(1) if sys.stdin.readable() else ""

    if len(s):
        c = ord(s) & 0xFF 
        return eof if sub_as_eof and c == 26 else c
    else:
        return eof
    
def default_write(n: int) -> None:
    if sys.stdout.writable():
        sys.stdout.write(chr(n))


def main(argv: List[str]):
    global eof, sub_as_eof

    min_size = 64
    size = 0x10000
    filename = ""
    debug = False

    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg in ["/nz", "-nz", "--zero-as-eof"]:
            eof = 0

            i += 1
            continue

        if arg in ["/ns", "-ns", "--sub-as-eof"]:
            sub_as_eof = True

            i += 1
            continue

        if arg in ["/d", "-d", "--enable-debug-command"]:
            debug = True

            i += 1
            continue

        prefixed = False
        prefix = ""
        for prefix0 in ["/size", "-size", "--memory-size"]:
            prefix = prefix0
            if arg.startswith(prefix):
                prefixed = True
                break

        if prefixed:
            if arg == prefix:
                if i + 1 < len(argv):
                    size = max(min_size, int(argv[i + 1]))
                    i += 2

                continue

            idx = len(prefix)
            if arg[idx] in ":=":
                idx += 1

            size = max(min_size, int(arg[idx:]))

            i += 1
            continue

        if not (arg[0] in "-/"):
            filename = arg

        i += 1

    if filename == "":
        print("python bfi.py [--memory-size=memory_size] [--zero-as-eof|-nz] [--sub-as-eof|-ns] src.bf")

        return 0

    try:
        Bfi.exec(filename, memory_size=size, read=default_read, write=default_write, debug=debug)

        return 0
    except Exception as e:
        # print(e)
        raise e
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))


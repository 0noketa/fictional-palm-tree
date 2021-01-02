from typing import cast, List, Dict
import sys
import io

from brainfuck_interpreter import Bfi

eof = 255

def default_read() -> int:
    global eof

    s = sys.stdin.read(1) if sys.stdin.readable() else ""
    return ord(s) & 0xFF if len(s) else eof

def default_write(n: int) -> None:
    if sys.stdout.writable():
        sys.stdout.write(chr(n))


def main(argv: List[str]):
    global eof

    min_size = 64
    size = 0x10000
    filename = ""

    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg in ["/z", "-z", "--zero-as-eof"]:
            eof = 0

            i += 1
            continue

        prefixed = False
        prefix = ""
        for prefix0 in ["/size", "-size", "--size"]:
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
        print("python [--size=memory_size] [--zero-as-eof] bfi.py src.bf")

        return 0

    try:
        Bfi.exec(filename, memory_size=size, read=default_read, write=default_write)

        return 0
    except Exception as e:
        # print(e)
        raise e
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))


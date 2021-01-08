
# optimized? Brainfuck interpreter
from typing import cast, Union, Tuple, List, Dict, Callable
import sys
import io

class InsCodes:
    def __init__(self) -> None:
        super().__init__()
        self.LOOP_START = ord("[")
        self.LOOP_END = ord("]")
        self.INC_PTR = ord(">")
        self.DEC_PTR = ord("<")
        self.INC_VAL = ord("+")
        self.DEC_VAL = ord("-")
        self.INPUT = ord(",")
        self.OUTPUT = ord(".")
        self.X_CLEAR = ord("0")
        self.X_SKIPR = ord("}")
        self.X_DEBUG = ord("!")
        self.X_MASK0 = ord("a")
        self.RANGE_X_MASKS = range(ord("a"), ord("z") + 1)

INS = InsCodes()


def default_read() -> int:
    s = sys.stdin.read(1) if sys.stdin.readable() else ""
    return ord(s) & 0xFF if len(s) else 255

def default_write(n: int) -> None:
    if sys.stdout.writable():
        sys.stdout.write(chr(n))

class Mask:
    """template for partial-update (can use SIMD?)\n
       from: eval_bf("[>+>>++<<<-]")\n
       to: for i in range(4): data[ptr + i] += [-1, 1, 0, 2][i]
    """

    def __init__(self, mask: List[int], anchor: int, next_ptr: int) -> None:
        super().__init__()

        self.mask = mask
        self.anchor = anchor
        self.next_ptr = next_ptr
        self.pairs = dict()

        for i in range(len(self.mask)):
            if self.mask[i] != 0:
                self.pairs[i] = self.mask[i]

        self.uses_dict = len(self.pairs) < len(self.mask) / 4

    def can_apply(self, data: List[int], ptr: int) -> bool:
        return (ptr + self.anchor >= 0
            and ptr + self.anchor + len(self.mask) <= len(data))

    def apply(self, data: List[int], ptr: int) -> int:
        if not (ptr in range(len(data))):
            raise Exception(f"applied mask was broken")

        if data[ptr] == 0:
            return ptr

        # when mask updates base pointer
        if self.next_ptr != 0:
            while data[ptr] != 0:
                if self.uses_dict:
                    for i in self.pairs.keys():
                        j = ptr + self.anchor + i

                        data[j] = (data[j] + self.mask[i]) & 0xFF
                else:
                    j = ptr + self.anchor

                    for i in range(len(self.mask)):
                        data[j] = (data[j] + self.mask[i]) & 0xFF

                        j += 1

                ptr += self.next_ptr

            return ptr

        diff = self.mask[-self.anchor]

        if diff == 255:
            n = data[ptr]
        else:
            current = (data[ptr] + diff) & 0xFF
            n = 1

            while current != 0:
                current = (current + diff) & 0xFF
                n += 1

                if n > 256:
                    raise Exception(f"infinite loop")

        if self.uses_dict:
            for i in self.pairs.keys():
                j = ptr + self.anchor + i

                data[j] = (data[j] + self.mask[i] * n) & 0xFF
        else:
            j = ptr + self.anchor
            for i in range(len(self.mask)):
                data[j] = (data[j] + self.mask[i] * n) & 0xFF

                j += 1

        return ptr

class Bfi:
    def __init__(self, src: str,
            memory_size: int = 0x10000,
            read: Callable[[], int] = default_read,
            write: Callable[[int], None] = default_write,
            debug=False) -> None:
        if debug:
            self.src = [ord(c) for c in src if c in "+-><[],.!"]
        else:
            self.src = [ord(c) for c in src if c in "+-><[],."]
        self.memory_size = memory_size
        self.read = read
        self.write = write
        self.debug = debug
        # masks
        self.masks = self.scan_masks()
        self.scan_clears()
        # Dict[ip: int, n_repeat: int] or large List[n_repeat: int]
        self.inc_pairs = self.scan_incs()

        self.bracket_pairs = self.scan_blocks()
        
        self.reinit()

    def scan_masks(self) -> List[Mask]:
        global INS
        r = []
        n_masks = 0

        i = 0
        while i < len(self.src):
            if n_masks >= 26:
                break

            mask = None
            if self.src[i] != INS.LOOP_START:
                i += 1
                continue

            mask, j = self.get_mask(i)

            if mask == None:
                i += 1
                continue

            self.src = self.src[:i] + [INS.X_MASK0 + n_masks] + self.src[j:]

            r.append(mask)
            n_masks += 1

            i = i + 1
            continue

        return r

    def get_mask(self, i: int) -> Tuple[Union[Mask, None], int]:
        """returns mask object"""
        global INS
        if not (i in range(len(self.src)) and self.src[i] == INS.LOOP_START):
            return (None, i + 1)

        lower = []
        higher = [0]
        ptr = 0

        j = i + 1
        while j < len(self.src):
            if self.src[j] == INS.LOOP_END:
                j += 1
                break
            elif self.src[j] == INS.INC_PTR:
                ptr += 1
                if abs(ptr) > len(higher) - 1:
                    higher.append(0)
            elif self.src[j] == INS.DEC_PTR:
                ptr -= 1
                if ptr < 0 and abs(ptr) > len(lower):
                    lower.append(0)
            elif self.src[j] == INS.INC_VAL:
                if ptr < 0:
                    lower[abs(ptr) - 1] = (lower[abs(ptr) - 1] + 1) & 0xFF
                else:
                    higher[ptr] = (higher[ptr] + 1) & 0xFF
            elif self.src[j] == INS.DEC_VAL:
                if ptr < 0:
                    lower[abs(ptr) - 1] = (lower[abs(ptr) - 1] - 1) & 0xFF
                else:
                    higher[ptr] = (higher[ptr] - 1) & 0xFF
            else:
                return (None, i + 1)

            j += 1

        if j - i < 5:
            return (None, i + 1)

        if ptr == 0 and higher[0] == 0:
            raise Exception(f"infinite loop")

        anchor = -len(lower)
        mask = [i & 0xFF for i in list(reversed(lower)) + higher]

        return (Mask(mask, anchor, ptr), j)

    def scan_clears(self):
        global INS
        i = 0
        while i < len(self.src) - 2:
            if self.src[i] == INS.LOOP_START and self.src[i + 2] == INS.LOOP_END:
                c = chr(self.src[i + 1])

                if c == ">":
                    self.src = self.src[:i] + [INS.X_SKIPR] + self.src[i + 3:]
                elif c in "+-":
                    self.src = self.src[:i] + [INS.X_CLEAR] + self.src[i + 3:]

            i += 1

    # merges ><+- and modifies src
    def scan_incs(self) -> Dict[int, int]:
        # r = dict()
        r = [0 for _ in range(len(self.src))]

        i = 0
        while i < len(self.src):
            if chr(self.src[i]) in "+-><":
                j = self.indexof_next(i)
                r[i] = j - i

                self.src = self.src[:i + 1] + self.src[j:]

            i += 1

        return r

    def indexof_next(self, i: int) -> int:
        if not (i in range(len(self.src)) and chr(self.src[i]) in "+-><"):
            return i + 1

        c = self.src[i]
        for i in range(i + 1, len(self.src)):
            if self.src[i] != c:
                return i

        return len(self.src)

    def scan_blocks(self) -> Dict[int, int]:
        global INS
        # r = dict()
        r = [0 for _ in range(len(self.src))]

        for i in range(len(self.src)):
            if self.src[i] == INS.LOOP_START:
                r[i] = self.indexof_end(i)
            elif self.src[i] == INS.LOOP_END:
                r[i] = self.indexof_start(i)
            else:
                continue

            if r[i] < 0:
                raise Exception("any open loop exist")

        return r

    def indexof_end(self, i: int) -> int:
        global INS
        if not (i in range(len(self.src)) and self.src[i] == INS.LOOP_START):
            return -2

        d = 0
        for j in range(i + 1, len(self.src)):
            if self.src[j] == INS.LOOP_START:
                d += 1
                continue
            if self.src[j] == INS.LOOP_END:
                if d > 0:
                    d -= 1
                    continue

                return j

        return -2

    def indexof_start(self, i: int) -> int:
        global INS
        if not (i in range(len(self.src)) and self.src[i] == INS.LOOP_END):
            return -2

        d = 0
        for j in range(i - 1, -1, -1):
            if self.src[j] == INS.LOOP_END:
                d += 1
                continue
            if self.src[j] == INS.LOOP_START:
                if d > 0:
                    d -= 1
                    continue

                return j

        return -2

    def run(self, no_init = True):
        if not no_init:
            self.reinit()

        while self.ip != -1:
            self.run1()

    def reinit(self):
        self.ip = 0
        self.ptr = 0
        self.data = [0 for _ in range(self.memory_size)]


    def run1(self):
        global INS

        if self.ip == -1:
            return

        if self.ip == len(self.src):
            self.ip = -1
            return

        ins = self.src[self.ip]

        # try:
        if True:
            if ins == INS.X_CLEAR:
                self.data[self.ptr] = 0
            elif ins == INS.INC_VAL:
                self.data[self.ptr] = (self.data[self.ptr] + self.inc_pairs[self.ip]) & 0xFF
                # self.data[self.ptr] += self.inc_pairs[self.ip]
            elif ins == INS.DEC_VAL:
                self.data[self.ptr] = (self.data[self.ptr] - self.inc_pairs[self.ip]) & 0xFF
                # self.data[self.ptr] -= self.inc_pairs[self.ip]
            elif ins == INS.INC_PTR:
                self.ptr += self.inc_pairs[self.ip]

                if self.ptr > self.memory_size:
                    raise Exception(f"out of memory")
            elif ins == INS.DEC_PTR:
                self.ptr -= self.inc_pairs[self.ip]

                if self.ptr < 0:
                    raise Exception(f"out of memory")
            elif ins == INS.INPUT:
                self.data[self.ptr] = self.read()
            elif ins == INS.OUTPUT:
                self.write(self.data[self.ptr])
            elif ins == INS.LOOP_START:
                if self.data[self.ptr] == 0:
                    self.ip = self.bracket_pairs[self.ip]
            elif ins == INS.LOOP_END:
                if self.data[self.ptr] != 0:
                    self.ip = self.bracket_pairs[self.ip]
            elif ins in INS.RANGE_X_MASKS:
                mask = self.masks[ins - INS.X_MASK0]

                if mask.can_apply(self.data, self.ptr):
                    self.ptr = mask.apply(self.data, self.ptr)
                else:
                    raise Exception(f"mask was broken")
            elif ins == INS.X_SKIPR:
                try:
                    self.ptr = self.data.index(0, self.ptr)
                except Exception:
                    raise Exception(f"out of memory")
            elif self.debug and ins == INS.X_DEBUG:
                print(f"""at {self.ip}({"".join(map(chr, self.src[self.ip:self.ip + 16]))}),\n  data: {self.data[0:32]}""")

                dumped = self.data[self.ptr:self.ptr + 32]
                print(f"  {self.ptr}: {dumped}")
            else:
                raise Exception(f"unknown instruction")

            self.ip += 1
        # except Exception as e:
        #     self.ip = -1
        #     dumped_src = self.src[self.ip:32] if self.ip in range(self.memory_size) else "bad ip"
        #     raise e
        #     raise Exception(f"error at {self.ip}th instruction({dumped_src}):\n{str(e)}")

    @staticmethod
    def exec(filename: str,
            memory_size: int = 0x10000,
            read: Callable[[], int] = default_read,
            write: Callable[[int], None] = default_write,
            debug=False) -> None:
        with io.open(filename) as f:
            src = f.read()

        bfi = Bfi(src, memory_size, read, write, debug)

        bfi.run()



# balanced ternary logic function composer
# for any of:
#   unary . unary = unary
#   unary . binary = binary
#
# most of operators are from
# https://homepage.cs.uiowa.edu/~dwjones/ternary/logic.shtml
#
# TriINTERCAL operators are treated with casting unsigned(2) as balanced(-1)
# https://esolangs.org/wiki/TriINTERCAL
#
# "complement" was used as binary xor for my old toy program. maybe any correct name exists,


to_btsym = (lambda x: {-1: "-", 0: "0", 1: "+"}[x])
to_utsym = (lambda x: {-1: "2", 0: "0", 1: "1"}[x])


buffer = (lambda x: x)

neg_ = (lambda x: (lambda y: x if y == 0 else -y))
proto_neg = (lambda x, y: neg_(y)(x))
bt_neg = neg_(0)
bt_pti = neg_(1)
bt_nti = neg_(-1)

inc = (lambda x: (x + 2) % 3 - 1)
dec = (lambda x: x % 3 - 1)

clamp_up = (lambda x: x if x == 1 else 0)
clamp_down = (lambda x: x if x == -1 else 0)

bt_min = (lambda x, y: min(x, y))
bt_max = (lambda x, y: max(x, y))

antimin = (lambda x, y: bt_neg(bt_min(x, y)))
antimax = (lambda x, y: bt_neg(bt_max(x, y)))

bt_xor = (lambda x, y: 0 if x == 0 or y == 0 else 1 if x != y else -1)

# symmetric
bt_sum = (lambda x, y: (x + y + 1) % 3 - 1)

# symmetric invertible function
bt_complement = (lambda x, y: -bt_sum(x, y))
bt_complement2 = (lambda x, y: x if x == y else list(set([-1, 0, 1]) - set([x, y]))[0])

# symmetric
bt_consensus = (lambda x, y: x if x == y else 0)
# symmetric
bt_any = (lambda x, y: x if x == y else x + y)

# symmetric
cmp = (lambda x, y: 1 if x == y else -1)
decode_n = (lambda x: cmp(x, -1))
decode_0 = (lambda x: cmp(x, 0))
decode_p = (lambda x: cmp(x, 1))

TriINTERCAL_and = (lambda x, y: 0 if 0 in (x, y) else -1 if -1 in (x, y) else 1)
TriINTERCAL_or = (lambda x, y: -1 if -1 in (x, y) else 1 if 1 in (x, y) else 0)
TriINTERCAL_but = bt_max
TriINTERCAL_sharkfin = bt_sum
# invertible
TriINTERCAL_what = (lambda x, y: y if x == 0 else (x + y + 2) % 3 - 1 if x == 1 else (x + y + 3) % 3 - 1)

unary_ops = {
    "buf": buffer,
    "neg": bt_neg,
    "not": bt_neg,
    "pti": bt_pti,
    "nti": bt_nti,
    "dec0": decode_0,
    "decn": decode_n,
    "decp": decode_p,
    "inc": inc,
    "dec": dec,
    "clampu": clamp_up,
    "clampd": clamp_down
}
binary_ops = {
    "min": bt_min,
    "and": bt_min,
    "max": bt_max,
    "or": bt_max,
    "amin": antimin,
    "antimin": antimin,
    "amax": antimax,
    "antimax": antimax,
    "xor": bt_xor,
    "_neg": proto_neg,
    "sum": bt_sum,
    "complement": bt_complement,
    "cons": bt_consensus,
    "consensus": bt_consensus,
    "any": bt_any,
    "cmp": cmp,
    "3i_and": TriINTERCAL_and,
    "3i_or": TriINTERCAL_or,
    "3i_but": TriINTERCAL_but,
    "3i_sharkfin": TriINTERCAL_sharkfin,
    "3i_what": TriINTERCAL_what
}

# generates 6 functions.
# every function does not change attributes by composition with "inc" or "dec" except "ivbl0".
# it means at least 3 symmetric invertible functions exist. "complement"="ivbl4" and its composition with "inc" or "dec".
def append_funcs():
    def table_to_func(table):
        table = [[x for x in xs] for xs in table]
        return (lambda x, y: table[x + 1][y + 1])

    def swapped(arr, at_=0, dist=1):
        arr = list(arr)
        t = arr[at_]
        arr[at_] = arr[(at_ + dist) % 3]
        arr[(at_ + dist) % 3] = t
        return arr

    row = [-1, 0, 1]

    n = 0

    for swap_cnt in range(2):
        for shift_dist in range(3):
            table = []
            for i in range(3):
                table.append(row)
                row = row[(shift_dist % 3):] + row[:(shift_dist % 3)]

            binary_ops[f"ivbl{n}"] = table_to_func(table)
            n += 1

        row = swapped(row, at_=0, dist=1)

append_funcs()

def make_table(f, argc=2, rank=1, args=[], table={}):
    if rank == argc:
        for i in [-1, 0, 1]:
            args2 = args + [i]
            r = f(*args2)
            
            table[i] = r

        return table

    for i in [-1, 0, 1]:
        table[i] = make_table(f, argc, rank + 1, args + [i], table={})

    return table


def is_symmetric(table):
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if table[i][j] != table[j][i]:
                return False

    return True

def get_type_of_invertible(table, argc=1):
    # rewrite all

    if argc == 1:
        attrs = [True, True]

        for i in [-1, 0, 1]:
            j = table[table[i]]
            k = table[j]
            if i != j:
                attrs[0] = False
            if i != k:
                attrs[1] = False

        return attrs

    attrs = [True, True, True, True, True, True]

    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if i != table[table[i][j]][j]:
                attrs[0] = False

            if i != table[j][table[i][j]]:
                attrs[1] = False

            if j != table[table[i][j]][i]:
                attrs[2] = False

            if j != table[i][table[i][j]]:
                attrs[3] = False

            if i != table[table[i][j]][table[j][i]]:
                attrs[4] = False

            if j != table[table[i][j]][table[j][i]]:
                attrs[5] = False

    return attrs

def is_invertible(table, argc=2, attrs=None):
    if attrs is None:
        attrs = get_type_of_invertible(table, argc=argc)

    return sum(attrs)

def print_table(f, argc, style=1, show_attrs=False):
    result = make_table(f, argc, args=[], table={})

    if show_attrs:
        ss = []

        if argc == 1 and is_invertible(result, argc=1):
            attrs = get_type_of_invertible(result, argc=1)
            if attrs[0]:
                ss.append("x = f.f(x)")
            if attrs[1]:
                ss.append("x = f.f.f(x)")

        if argc == 2:
            symmetric = is_symmetric(result)
            if symmetric:
                ss.append("f(x, y) = f(y, x)")

            if is_invertible(result, argc=2):
                attrs = get_type_of_invertible(result, argc=2)
                if attrs[0]:
                    ss.append("x = f(f(x, y), y)")
                if not symmetric:
                    if attrs[1]:
                        ss.append("x = f(y, f(x, y))")
                    if attrs[2]:
                        ss.append("y = f(f(x, y), x)")
                    if attrs[3]:
                        ss.append("y = f(x, f(x, y))")
                if attrs[4]:
                    ss.append("x = f(f(x, y), f(y, x))")
                if not symmetric and attrs[5]:
                    ss.append("y = f(f(x, y), f(y, x))")

        if len(ss):
            print("attributes:")
            print("\n".join(map(lambda x: "  " + x, ss)) + "\n")
            print("----")
 
    if style in range(2, 4):
        ternary_range = [0, 1, -1]
        to_sym = to_utsym
    else:
        ternary_range = [-1, 0, 1]
        to_sym = to_btsym

    if style < 4 and argc == 2:
        if style % 2 == 1:
            print("  " + "".join(map(to_sym, ternary_range)))
            print("")
        for row in ternary_range:
            if style % 2 == 1:
                s = to_sym(row) + " "
            else:
                s = ""

            for col in ternary_range:
                s += to_sym(result[row][col])

            print(s)
        return
 
    if style < 4 and argc == 1:
        for row in ternary_range:
            if style % 2 == 1:
                s = to_sym(row) + " "
            else:
                s = ""

            s += to_sym(result[row])

            print(s)
        return
 
    if style == 4 and argc == 2:
        for row in ternary_range:
            for col in ternary_range:
                s = f"{to_sym(row)}{to_sym(col)} "
                s += to_btsym(result[row][col])

                print(s)
        return
 
    if style == 4 and argc == 1:
        for row in ternary_range:
            s = f"{to_sym(row)} "
            s += to_sym(result[row])

            print(s)
        return

    print("style error")

# maybe Python's builtin something exists
def composite_unary(f0, f1):
    return (lambda x: f0(f1(x)))
def composite_unary_and_binary(f0, f1):
    return (lambda x, y: f0(f1(x, y)))


if __name__ == "__main__":
    table_style = 1
    show_attrs = False

    while True:
        cmds = input().strip().split()
        unknown_ops = []
        err = False

        if len(cmds) == 0:
            continue

        if cmds[0] == "bye":
            break

        if cmds[0] == "attrs":
            show_attrs = True
            continue

        if cmds[0] == "noattrs":
            show_attrs = False
            continue

        if cmds[0] == "help":
            print("repl: attrs noattrs style help bye")
            print("unary: " + " ".join(unary_ops.keys()))
            print("binary: " + " ".join(binary_ops.keys()))
            continue

        if cmds[0] == "style":
            if len(cmds) < 2:
                print("style command requres 1 argument (0-4)")
                print("""style [number]
    style0: col x row table
    style1: style0 with labels
    style2: style0 with unsigned ternary
    style3: style1 with unsigned ternary
    style4: col+row as key""")

                continue

            table_style = int(cmds[1])
            continue

        fs = []
        for key in cmds[: -1]:
            if key not in unary_ops:
                print(f"unknown op {key}")
                err = True
                break

            fs.append(unary_ops[key])

        if err:
            continue

        ff_name = cmds[-1]
        if ff_name in unary_ops:
            first = unary_ops[ff_name]

            f = first
            for i in reversed(fs):
                f = composite_unary(i, f)

            print_table(f, argc=1, style=table_style, show_attrs=show_attrs)
        elif ff_name in binary_ops:
            first = binary_ops[ff_name]

            f = first
            for i in reversed(fs):
                f = composite_unary_and_binary(i, f)

            print_table(f, argc=2, style=table_style, show_attrs=show_attrs)
        else:
            print(f"unknown op {ff_name}")


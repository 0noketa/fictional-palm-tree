# many-valued logic symmetric invertible function generator
#
# currently this program generrates n functions on n-any logic.
# besides if n = m ** o and m is prime number, additional m^2 functions.



def is_xor(table, radix):
    for x in range(radix):
        for y in range(radix):
            if table[x][y] != table[y][x] or x != table[table[x][y]][y]:
                return False
    return True

def apply_inc_to_table(table, radix):
    for x in range(radix):
        for y in range(radix):
            table[x][y] = (table[x][y] - 1) % radix

def make_xor(radix):
    table = []
    for i in range(radix):
        row = list(reversed(range(radix)))
        row = row[i:] + row[:i]

        table.append(row)

    return table

def print_table(table, radix):
    def to_sym(i):
        if radix < 36:
            if i > 9:
                return chr(65 + i - 10)
            else:
                return str(i)

        if radix < 100:
            return f"{i:2} "

        if radix < 1000:
            return f"{i:3} "

        return f"{i},"

    for i in range(radix):
        s = "".join(map(to_sym, table[i]))
        print(s)

def get_prime_factors(n):
    results = []

    while n % 2 == 0:
        results.append(2)

        n >>= 1
        if n == 1:
            break

    for i in range(3, n + 1, 2):
        while n % i == 0:
            results.append(i)
            n //= i
            if n == 1:
                return results

    return results

def func_to_table(f, radix):
    return [[f(x, y) for x in range(radix)] for y in range(radix)]

def make_composite_table(radix, sub_table, sub_radix, cols):
    def f(x, y):
        result = 0
        for i in range(cols):
            result += sub_table[x // (sub_radix ** i) % sub_radix][y // (sub_radix ** i) % sub_radix]  * (sub_radix ** i)

        return result

    return func_to_table(f, radix)

if __name__ == "__main__":
    import sys
    table_style = 1
    show_attrs = False
    radix = 3
    n = 0

    if len(sys.argv) > 1:
        if sys.argv[1].endswith("help"):
            print("this [n_elements] [n_function]")
            sys.exit(0)

        radix = int(sys.argv[1])

    if len(sys.argv) > 2:
        n = int(sys.argv[2])
        
    table = make_xor(radix)

    for i in range(radix):
        if i == n:
            print_table(table, radix)
            sys.exit(0)

        apply_inc_to_table(table, radix)


    pfs = get_prime_factors(radix)

    if len(set(pfs)) == 1:
        pf = list(pfs)[0]
        sub_table = make_xor(pf)

        n -= radix
        for i in range(pf):
            table = make_composite_table(radix, sub_table, pf, len(pfs))

            for j in range(radix // pf):
                if j == n:
                    print_table(table, radix)
                    sys.exit(0)

                for k in range(pf):
                    apply_inc_to_table(table, radix)

            apply_inc_to_table(sub_table, pf)
            n -= radix // pf


    print("invalid func number")
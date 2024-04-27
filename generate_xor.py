# many-valued logic symmetric invertible function generator


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
        n = int(sys.argv[2]) % radix
        
    table = make_xor(radix)

    for i in range(n):
        apply_inc_to_table(table, radix)
    
    print_table(table, radix)

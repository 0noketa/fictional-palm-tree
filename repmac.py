
"""simple replacement macro languages

default_language shortens regex to match source-codes.

default_language:

    `F: signed float

    `D: signed dec int

    `U: unsigned dec int

    `H: unsigned hex int

    `N: `F or `U or `H

    `S: C string

    `I: C-like id (accepts mid dots)

    `V: `N or `S or `I

    `A: C-arguments (excludes bracket)

    `P: id list
"""

import re

def singleline(s:str) -> str:
    """split at eol, strip every part, and then join them.
    """
    return "".join(map(lambda x: x.strip(), s.split("\n")))

default_macro = [
    ["`A", singleline("""
        (?:`V(?:\s*\,\s*`V)*)
    """)],
   ["`P", singleline("""
        (?:`I(?:\s*\,\s*`I)*)
    """)],
    ["`V", """
        (?:`N|`S|`I)
    """.strip()],
    ["`N", singleline("""
        (?:`F|`D|`H)
    """)],
    ["`F", singleline("""
        (?:(?:|\+|\-)
            (?:`U(?:|\.(?:|`U))
            |\.`U
            )
            (?:
            |[eE][\+\-][0-9]+
            )
        |`D
        )
    """)],
    ["`D", "(?:(?:[\\+\\-]|)`U)"],
    ["`U", "(?:0|[1-9][0-9]*)"],
    ["`H", "(?:0x[0-9a-fA-F]+|[0-9a-fA-F]+[hH])"],
    ["`S", singleline("""
        (?:(?:\\"(?:\\\"|[^\\"])*\\")
        |(?:\\'(?:\\\'|[^\\"])*\\')
        )
    """)],
    ["`I", singleline("""
        (?:[a-zA-Z_]+(?:|[a-zA-Z0-9_\.]*[a-zA-Z0-9_]+))
    """)],
    ["``", "`"]
]


def translate(pattern:str, macro:list=default_macro) -> str:
    """script pattern written in macro to regex
    """
    try:
        for k, v in macro:
            pattern:str = pattern.replace(k, v)

        return pattern
    except Exception:
        return pattern

def compile(pattern:str, macro:list=default_macro):
    """translates and compiles as regex
    """
    rx = translate(pattern, macro=macro) if type(macro) == list else pattern

    return re.compile(rx)

def match(pattern:str, s:str, macro:list=default_macro):
    """translates and passes to re.match
    """
    return re.match(translate(pattern, macro=macro), s)

def eject(pattern:str, s:str, macro:list=default_macro) -> tuple:
    """translates and passes to re.match, and then takes groups
    """
    rx = re.compile(translate(pattern, macro=macro))
    mch = rx.match(s)

    return map(str, mch.groups()) if mch else tuple([None for _ in range(rx.groups)])


default_language = [
    ["label", compile(singleline("""
        ^\s*(`I)\s*(?:\:\s*|)$
    """))],
    ["assign", compile(singleline("""
        ^\s*(`I)\s*([\+\-\*\/\%\&\|\$\?]|)\=\s*(`V)\s*$
    """))],
    ["if", compile(singleline("""
        ^\s*(`I)\s*if\s*(`V)\s*([\=\#\>\<])\s*(`V)\s*$
    """))],
    ["ifdef", compile(singleline("""
        ^\s*(`I)\s*if(n|)def\s*(`I)\s*$
    """))],
    ["ret", compile(singleline("""
        ^\s*ret\s*(`V)\s*$
    """))],
    ["call", compile(singleline("""
        ^\s*call\s*(`I)\s*$
    """))]
]

def parse_one(s:str, lang:list=default_language) -> tuple:
    """simple parser for EOL-separated languages
    """
    for k, v in lang:
        m = v.match(s)

        if m:
            v2 = tuple(map(str, m.groups()))

            return (k, v2)
    
    return ("", (s,))

def default_eval(s:str, vs:dict={}) -> dict:
    """micro interpreter. returns modified dictionary. 
    
    s: program

    vs: variables
    """

    if s == None:
        s = """
            main if 0=0
            rep:
                sym?="?": len?=4
                i=0: r=""
            rep.loop: r+=sym: i+=1
                rep.loop if i<len
                ret r
            main:
                call rep: x=r
                sym$="!": len$=8: call rep: y=r
                sym$="#": len$=6: call rep: z=r
                r="check x, y and z"
                end
        """

    c = []
    for i in re.split("\\n|\:", s):
        tpl = parse_one(i)
        t, a = tpl

        if t != "":
            c += [tpl]

    i = 0
    j = len(c)
    tmp = {}

    def goto_label(lbl):
        for n in range(j):
            t2, a2 = c[n]

            if t2 == "label" and a2[0] == lbl:
                return n
        
        return j

    def get_value(v):
        if v == "None":
            return None
        elif v[0] in "0123456789+-.":
            return float(v)
        elif v[0] in "\"":
            return (v[1:-1])
        elif v in vs.keys():
            return vs[v]
        else:
            return 0

    def set_value(v, op, n):
        n = get_value(n)

        if op == "$":
            tmp[v] = n

            return

        if v not in vs.keys() or vs[v] == None:
            if op == "" or op == "?":
                vs[v] = n

                return

        if v in vs.keys() and vs[v] != None:
            if n == None:
                vs[v] = None

                return
            
            n = type(vs[v])(n)

        if op == "+":
            n = vs[v] + n
        elif op == "-":
            n = vs[v] - n
        elif op == "*":
            n = vs[v] * n
        elif op == "/":
            n = vs[v] / n
        elif op == "%":
            n = vs[v] % n
        elif op == "?":
            return

        vs[v] = n

    stk = []
    steps = 0

    while i < j and steps < 65536:
        steps += 1
        t, a = c[i]

        if t == "if": 
            left = get_value(a[1])
            right = get_value(a[3])
            op = a[2]

            if (op == "=" and left == right
                    or op == "#" and left != right
                    or op == "<" and left < right
                    or op == ">" and left > right):
                i = goto_label(a[0])

                continue
        elif t == "ifdef": 
            if (a[2] in vs.keys() and vs[a[2]] != None) == (a[1] == ""):
                i = goto_label(a[0])

                continue
        elif t == "assign":
            set_value(a[0], a[1], a[2])
        elif t == "call":
            if len(stk) > 32: break

            stk += [(i + 1, vs)]
            vs = tmp
            i = goto_label(a[0])

            continue
        elif t == "ret":
            if len(stk) == 0: break

            v = get_value(a[0])
            i, vs = stk.pop()
            tmp = {}
            vs["r"] = v

            continue

        i += 1
    
    return vs

if __name__ == "__main__":
    s = ""

    try:
        while True:
            s2 = input().strip()

            if s2 == "end": break

            s += s2 + "\n"
        
        d = default_eval(s)

        print(d)
    except Exception as e:
        print("error:" + str(e))


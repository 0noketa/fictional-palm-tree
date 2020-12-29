
import sys
import os
import io
import re
import pych

def pad(s, i):
    s = list(s)

    if len(s) < i:
        return s + [None for j in range(i - len(s))]
    else:
        return s

def types_are(ts, vs):
    check = (lambda t, v:
            True
                if t == None
            else len(list(map(lambda t: type(v) != t, t))) > 0
                if type(t) == list
            else type(v) == t)

    vs = list(vs)
    vs = pad(vs, len(ts))

    if (type(ts) != type(vs) 
            or type(ts) != list):
        return False

    vs = pad(vs, len(ts))

    for t, v in zip(ts, vs):
        if t != None and not check(t, v):
            return False

    return True

_ = None

def builtin_re(*args):
    """(str)re.Pattern re;"""
    types = (lambda x: types_are(x, args))

    if types([str, _]):
        return re.compile(*args)
    else:
        return None

def builtin_all(*args):
    types = (lambda x: types_are(x, args))
    o, ptn = pad(args, 2)

    if len(args) == 0:
        o = "."
        ptn = builtin_re(".*")
        args = [o, ptn]
    elif types([str]):
        ptn = o
        o = "."
        args = [o, ptn]
    elif types([re.Pattern]):
        ptn = args[0]
        o = "."
        args = [o, ptn]
    elif types([re.Pattern, _]):
        ptn, o = args
        args = [o, ptn]

    r = []

    if types([_, re.Pattern]):
        if types([dict, _]):
            r = filter(lambda k, _: ptn.match(k), o)
        elif types([list, _]):
            r = filter(lambda v: ptn.match(v), o)
        elif types([str, _]):
            r = filter(lambda v: ptn.match(v), builtin_ls(o))
    elif types([str, str]):
        r = filter(lambda v: re.match(ptn, v), builtin_ls(o))

    r = list(r)

    return r

def builtin_exists(*args):
    """/* finds elements. returns number of elements */
       (re.Pattern)int exists;
       (str)int exists;
       (re.Pattern, str dir)int exists;
       (str, str dir)int exists;
    """
    types = (lambda x: types_are(x, args))
    s, d = pad(args, 2)

    if d == None:
        d = "."
        args = [s, d]

    if s == None:
        return False
    
    if types([[str, re.Pattern], str]):
        return len(builtin_all(d, s)) > 0

    return False

def builtin_isdir(*args):
    """/* checks element type */
       (str)bool isdir;
    """
    types = (lambda x: types_are(x, args))
    s, d = pad(args, 2)

    if d == None:
        d = "."

    if s == None:
        return False

    for i in os.scandir(d):
        if i.name == s and i.is_dir():
            return True

    return False

def builtin_cd(*args):
    """/* changes and returns cwd */
       ()str cd;
       (str new_dir)str cd;
    """
    types = (lambda x: types_are(x, args))
    d = pad(args, 1)[0]

    if d == None:
        d = "."
        args = [d]
    
    if types([str]):
        try:
            os.chdir(d)
        except:
            pass

    return os.getcwd()

def builtin_ls(*args):
    """/* lists elements in dir. */
       ()List[str] ls;
       (str dir)List[str] ls;
    """
    types = (lambda x: types_are(x, args))
    d = pad(args, 1)[0]

    if d == None:
        d = "."
    
    try:
        return os.listdir(d)
    except:
        return []

def builtin_obj(*args):
    """/* mixing object */\n
       (...dict)dict obj;"""
    d = dict(args[0]) if len(args) else dict()

    for i in args[1:]:
        d.update(i)

    return d

def builtin_member(*args):
    """/* extends object with new member */\n
       (dict, str, any)dict member;"""
    types = (lambda x: types_are(x, args))
    d, k, v = pad(args, 3)

    if types([dict, str, _]):
        d[k] = v
    
    return d

def builtin_without(*args):
    """/* removes member(s) from object by key */\n
       (dict, str key)dict without;\n
       (dict, re.Pattern keys)dict without;\n
       (dict, List[str] keys)dict without;\n
       /* removes value(s) from list */\n
       (list, any)list without;\n
       (list, re.Pattern)list without;\n
       (list, list sub_pattern)list without;\n"""
    types = (lambda x: types_are(x, args))
    d, k = pad(args, 2)

    if types([dict, _]):
        d = dict(d)
    elif types([list, _]):
        d = list(d)

    if types([dict, str]):
        if k in d.keys():
            d.pop(k)
    elif types([dict, list]):
        for i in k:
            if i in d.keys():
                d.pop(i)
    elif types([dict, re.Pattern]):
        for i in d.keys():
            if k.match(i):
                d.remove(i)
    elif types([list, list]):
        for i in k:
            if i in d:
                d.remove(i)
    elif types([list, re.Pattern]):
        for i in d:
            if k.match(i):
                d.remove(i)
    elif types([list, _]):
        if k in d:
            if k in d:
                d.remove(k)

    return d

def builtin_set(*args):
    """/* rewrites member of object (overwrites object). returns value. */\n
       (dict, str key, any value)any set;\n
       (list, int index, any value)any set;
    """
    types = (lambda x: types_are(x, args))
    d, k, v = pad(args, 3)

    if types([dict, str, _]):
        d[k] = v
    if types([list, int, _]):
        d[k] = v
    
    return v

def builtin_get(*args):
    """/* gets member of object. returns None if key was invalid. */\n
       (dict, str key)any get;\n
       (list, int index)any get;
    """
    types = (lambda x: types_are(x, args))
    d, k = pad(args, 2)

    if (types([dict, str])
            or types([list, int])):
        return d[k]

    return None

def builtin_has(*args):
    """/* checks existance of member */\n
       (dict, str key)bool has;\n
       (list, re.Pattern value)bool has;  /* expects List[str] */\n
       (list, any value)bool has;
       (str, re.Pattern substring)bool has;
       (str, str substring)bool has;
    """
    types = (lambda x: types_are(x, args))
    d, k = pad(args, 2)
    
    if types([dict, str]):
        return k in d.keys()
    if types([list, re.Pattern]):
        return len(filter(lambda x: k.match(x), d)) > 0
    if types([list, _]):
        return k in d
    if types([str, [str, re.Pattern]]):
        return len(builtin_all(d, k)) > 0

    return False

def builtin_keys(*args):
    """/* keys */\n
       (dict)List[str] keys;\n
       (list)range keys;\n
    """
    if len(args) == 0:
        return []
    
    o = args[0]

    if type(o) == dict:
        return list(o.keys())
    elif type(o) == list:
        return range(len(o))
    else:
        return []

def win_esc(s):
    """/* encodes with cmd.exe escape-sequences */\n
       (str)str esc;\n
    """
    if re.match(" ^@\\\"\\|&!%\\(\\)<>\\.,*?:;",s):
        for i in list(" ^@\"|&!%()<>.,*?:;"):
            s = s.replace(i, "^" + i)
            
    return s

def any_esc(s):
    """/* encodes with escape-sequences */\n
       (str)str esc;\n
    """
    if re.match("\\\"", s):
        s = "\"" + s.replace("\"", "\\\"") + "\""
            
    return s

def builtin_exec(*args):
    """/* executes command. returns True if exit-code was 0. */\n
       (str commandline)bool exec;\n
       (str command, List[str] args)bool exec;\n
       /* ex: () exec("cmd1")or("cmd2") andthen("cmd2_1")or("cmd2_2") orelse("cmd3_1")or("cmd3_2")\n
        * or: ("cmd1" exec || "cmd2" exec) && ("cmd2_1" exec || "cmd2_2" exec) || "cmd3_1" exec || "cmd3_2" exec\n
        */
    """
    types = (lambda x: types_are(x, args))

    c, a = pad(args, 2)

    if types([str, list]):
        if os.name == "nt":
            a = map(win_esc, a)
        else:
            a = map(any_esc, a)

        return os.system(c + " " + " ".join(list(a))) == 0
    elif types([str, str]):
        return os.system(c + " " + a) == 0
    else:
        return False

def builtin_andthen(*args):
    """/* executes command if condition is True */\n
       (bool condition, str commandline)None andthten;\n
       (bool condition, str command, List[str] args)None andthen;\n
    """
    types = (lambda x: types_are(x, args))
    b, c, a = pad(args, 3)

    if types([bool, str, list]):
        if b:
            return builtin_exec(c, a)

    return False

def builtin_orelse(*args):
    """/* executes command if condition is False */\n
       (bool condition, str commandline)None orelse;\n
       (bool condition, str command, List[str] args)None orelse;\n
    """
    types = (lambda x: types_are(x, args))
    b, c, a = pad(args, 3)

    if types([bool, str, list]):
        if not b:
            return builtin_exec(c, a)

    return False

def builtin_putln(*args):
    """/* Python\'s print(). returns first arg or None. */\n
       (...any)any putln;
    """
    print(*args)

    return args[0] if len(args) else None

def builtin_exit():
    """/* stops interpreter */\n
       ()None exit;\n
    """
    global interactive
    interactive = False

    return "bye"

def main(argv):
    global interactive

    src = """
        stdout putln("Hello, world!")
        """
    interactive = False

    if 1 < len(argv):
        if argv[1] == '-i':
            interactive = True
        else:
            with io.open(argv[1]) as f:
                src = f.read()

    native_funcs = {
        're': builtin_re,
        'all': builtin_all,
        'exists': builtin_exists,
        'isdir': builtin_isdir,
        'cd': builtin_cd,
        'ls': builtin_ls,
        'obj': builtin_obj,
        'member': builtin_member,
        'without': builtin_without,
        'set': builtin_set,
        'get': builtin_get,
        'keys': builtin_keys,
        'has': builtin_has,
        'exec': builtin_exec,
        'andthen': builtin_andthen,
        'orelse': builtin_orelse,
        'putln': builtin_putln,
        'exit': builtin_exit
    }
    with_vars = {
        'args': argv[2:]
    }

    chi = pych.Pych(native_funcs, with_vars)

    if interactive:
        sys.stdout.write('>')
        src = input().strip()
        interactive = True

        while interactive:
            if src == ";;":
                src = ""
                continue

            if chi.load(src)[0]:
                print(chi.eval(src))
                src = ""
                sys.stdout.write('>')
            else:
                src = src + " "
                sys.stdout.write(' ')

            if interactive:
                src = src + input().strip()
    else:
        r = chi.eval(src)

if __name__ == "__main__":
    sys.exit(main(sys.argv))

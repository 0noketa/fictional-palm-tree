
# dynamic subset
# no function can be defined

import re

class Pych:
	def __init__(self, native_funcs={}, with_vars={}):
		self.pattern = """
			(
			[a-zA-Z_]+[a-zA-Z_0-9]*|
			[1-9]+[0-9]*|0|
			0b[01]+|0x[0-9A-F]+|
			"[^"']*"|
			'[^\\]'|
			'\\'|
			'\\[.]'|
			'\\[x][0-9A-F]{1,2}'|
			'\\[b][01]{1,8}'|
			\<[a-zA-Z_0-9\.\/]*\>|
			\>\>\<|\>\<\<|
			[\&\|\?\+\-\*\/\<\=\>\:\.]{1,2}|
			\!\=|\<\=|\>\=|
			[\(\)\{\}\[\]\,\%
			\^\;\$\`\@\~]
			)
			""".replace('\n', "").replace('\t', "")
		self.keyword = [
			"let", "with", "on",
			"if", "then", "else",
			"for", "filter", "map",
			"as", "is", "to",
			"and", "or",
			";", ",",
			"import", "local", "global"]
		self.native_funcs = {
			'len': len,
			'eq': (lambda x, y: x == y),
			'lt': (lambda x, y: x < y),
			'gt': (lambda x, y: x > y),
			'is_mod': (lambda x, y: x % y == 0),
			'to_int': int,
			'to_str': str,
			'to_char': chr,
			'to_list': list,
			'to_bool': (lambda x: True if x else False),
			'in': (lambda x, y: x in y),
			'has': (lambda x, y: y in x),
			'starts_with': (lambda x, y: x.startswith(y)),
			'ends_with': (lambda x, y: x.endswith(y)),
			'index_of': (lambda x, y: x.find(y)),
			'last_index_of': (lambda x, y: x.rfind(y)),
			'slice': (lambda x, y, z: x[y:z]),
			'split': (lambda x, y: x.split(y)),
			'join': (lambda x, y: x.join(y)),
			'trim': (lambda x: x.strip()),
			'ld': (lambda x, y: x[y]),
			'st': (lambda x, y, z: x[0:y]+[z]+x[y+1:]),
			'not': (lambda x: not x)}

		self.funcs = {}
		self.vars = with_vars.copy()

		for i in native_funcs.keys():
			self.native_funcs[i] = native_funcs[i]

	def load(self, src):
		x0 = map((lambda x: x.strip()),
			re.split(self.pattern, src))

		self.code = [x for x in x0 if 0 < len(x)]

		success, src2, node = self.validate_expr(self.code)
		if success:
			#print(node)
			return (True, src2, node)
		else:
			return (False, src, "")

	def eval(self, src, with_vars=None):
		success, src2, node = self.load(src)

		if success:
			return self.run(node, with_vars)
		else:
			return None

	def run_unpack(self, e, with_vars=None):
		r = self.run(e, with_vars)

		if self.typeof_node(r) == "tuple":
			return r[1:][-1]
		else:
			return r

	def run(self, e, with_vars=None):
		if with_vars != None:
			vars0 = self.vars
			self.vars = with_vars.copy()
			self.vars['#super'] = vars0

		t = self.typeof_node(e)

		r = e

		if t == "filter":
			if len(e) == 4:
				lst = self.run_unpack(e[3])

				id = e[1]
				r = [] if type(lst) == list else ""

				for i in lst:
					if self.run_unpack(e[2], {id : i}):
						if type(r) == list:
							r.append(i)
						else:
							r = r + str(i)
			else:
				r = None
		elif t == "map":
			if len(e) == 4:
				lst = self.run_unpack(e[3])
				r = [] if type(lst) == list else ""

				id = e[1]

				for i in range(len(lst)):
					x = self.run_unpack(e[2], {id : lst[i]})

					if type(lst) == list:
						r = r + [x]
					else:
						r = r + x
			else:
				r = None
		elif t == "for":
			if len(e) == 5:
				id = e[1]

				rng = range(self.run_unpack(e[2]),
					self.run_unpack(e[3]))

				r = []

				for i in rng:
					v = self.run_unpack(e[4], {id: i})

					r.append(v)
			else:
				r = None

		elif t == "let":
			vs = {}

			if 1 < len(e):
				for i in e[1]:
					vs[i['id']] = self.run_unpack(i['val'])

			if 2 < len(e):
				if vs.keys() == 0:
					vs = self.vars

				r = self.run_unpack(e[2], vs)
			else:
				r = None
		elif t == "call":
			f = self.get_builtin_func(e[1])
			args = [self.run(x) for x in e[2]]

			if 3 < len(e):
				args2 = args + [self.run(x) for x in e[3][0]]
			else:
				args2 = args

			r = f(*args2) if f != None else None

			if 3 < len(e) and 1 < len(e[3]):
				# "and/or" chainer
				if type(r) == bool:
					excepts_or = False

					for cell in e[3][1:]:
						nexus, args3 = cell[0], cell[1]

						if excepts_or:
							if nexus == "or":
								excepts_or = False
							else:
								continue

						if nexus == "and" and not r:
							# skip "and" until "or"
							excepts_or = True
							continue

						if nexus == "or" and r:
							# "or" can not nest
							break

						args2 = args + [self.run(x) for x in args3]

						if len(cell) == 3:
							f = self.get_builtin_func(cell[2])

						r = f(*args2) if f != None else None
				else:
					# nexus type "and" makes list if function does not return boolean
					r0 = r
					r = [r0]

					for cell in e[3][1:]:
						nexus, args3 = cell[0], cell[1]

						if nexus == "or":
							# error
							break

						args2 = args + [self.run(x) for x in args3]

						if len(cell) == 3:
							f = self.get_builtin_func(cell[2])

						r0 = f(*args2) if f != None else None

						r.append(r0)

		elif t in ["list", "tuple"]:
			if len(e) > 1:
				lst = [self.run(x) for x in e[1:]]
			else:
				lst = []

			r = (lst if t == "list"
				else lst[-1] if len(lst)
				else None)
		elif t == "then":
			if self.run_unpack(e[1]):
				r = self.run(e[2])
			elif 2 < len(e):
				r = self.run(e[3])
			else:
				r = False
		elif t == "||":
			r = False
			for i in range(1, len(e)):
				r = self.run_unpack(e[i])
				if r == True:
					break
		elif t == "&&":
			r = True
			for i in range(1, len(e)):
				r = self.run_unpack(e[i])
				if r == False:
					break
		elif t in ['+', '-', '*', '/', '%']:
			arg1 = self.run_unpack(e[1])
			arg2 = self.run_unpack(e[2])

			r = (arg1 + arg2 if t == '+' else
				arg1 - arg2 if t == '-' else
				arg1 * arg2 if t == '*' else
				(0 if arg2 == 0 else arg1 / arg2)
					if t == '/' else
				arg1 % arg2 if t == '%' else
				arg1)
		elif t == list:
			r = ["runtime-error"]
		else:
			if t == str:
				if e.isidentifier():
					r = self.get_from_chained(e, dictionary=self.vars)
				elif e.startswith('\"'):
					r = e[1:-1]
				else:
					r = e

		if with_vars != None:
			self.vars = vars0

		return r

	def get_builtin_func(self, name):
		return (self.native_funcs[name]
				if name in self.native_funcs.keys()
			else None)

	def get_from_chained(self, name,
			value=0, dictionary=None, set_value=False):
		d = dictionary

		if d == None:
			return None

		if name in d.keys():
			return d[name]

		while '#super' in d.keys():
			d = d['#super']

			if name in d.keys():
				if set_value:
					d[name] = value

				return d[name]

		return None

	def set_to_chained(self, name, value, dictionary=None):
		return self.get_from_chained(name, value,
				dictionary=dictionary,
				set_value=True)


	# every part of parser returns triple (success, rest, node)
	# if success == True, parent can continue after rest.
	# or else, can back-track.


	def validate_expr(self, src):
		if 0 < len(src):
			if src[0] == ";":
				src = src[1:]

		return self.validate_for_expr(src)

	def validate_for_expr(self, src):
		err = (False, src, "")

		success, src, node = self.validate_keyword(src, "for")

		if not success:
			return self.validate_filter(src)

		success, src2, node = self.validate_id(src)

		if not success or len(src2) == 0:
			return err

		success, src3, node2 = self.validate_expr(src2)

		if not success or len(src3) == 0:
			return err

		success, src4, node3 = self.validate_expr(src3)

		if not success or len(src4) == 0:
			return err

		success, src5, node4 = self.validate_expr(src4)

		if not success:
			return err

		return (success, src5, ["for", node, node2, node3, node4])

	def validate_filter(self, src):
		err = (False, src, "")

		success, src2, _ = self.validate_keyword(src, "filter")

		if not success:
			return self.validate_map(src)

		success, src2, node = self.validate_id(src2)

		if not success:
			return err

		success, src3, node2 = self.validate_expr(src2)

		if not success:
			return err

		success, src4, node3 = self.validate_expr(src3)

		if not success:
			return err
		else:
			return (True, src4, ["filter", node, node2, node3])

	def validate_map(self, src):
		err = (False, src, "")

		success, src2, _ = self.validate_keyword(src, "map")

		if not success:
			return self.validate_let(src)

		success, src2, node = self.validate_id(src2)

		if not success:
			return err

		success, src3, node2 = self.validate_expr(src2)

		if not success:
			return err

		success, src4, node3 = self.validate_expr(src3)

		if not success:
			return err
		else:
			return (True, src4, ["map", node, node2, node3])

	def validate_let(self, src):
		err = (False, src, "")

		success, src2, _ = self.validate_keyword(src, "let")

		if not success:
			return self.validate_then(src)

		vs = []
		node = ["let", vs]


		while 0 < len(src2):
			success, src3, node2 = self.validate_id(src2)

			if not success:
				return err

			success, src4, node3 = self.validate_expr(src3)

			if not success:
				return err

			vs.append({'id':node2, 'val':node3})

			if len(src4) == 0:
				if len(node) == 3:
					return (success, src4, node)
				else:
					return err

			src2 = src4

			if src2[0] != ",":
				break

			src2 = src2[1:]

		if 0 < len(src2):
			success, src3, node2 = self.validate_expr(src2)

			if not success:
				return err

			node.append(node2)
			src2 = src3
		elif len(node) != 3:
			return err

		return (success, src2, node)

	def validate_then(self, src):
		err = (False, src, "")

		success, src2, node = self.validate_or(src)

		if not success:
			return err
		elif len(src2) == 0:
			return (success, src2, node)
		elif src2[0] != "then":
			return (success, src2, node)

		node2 = ["then", node]
		src3 = src2[1:]

		# then

		success, src4, node3 = self.validate_expr(src3)

		if not success:
			return err

		node2.append(node3)

		if len(src4) == 0:
			return err
		elif src4[0] != "else":
			return (success, src4, node2)

		src5 = src4[1:]

		# else

		success, src6, node4 = self.validate_expr(src5)

		if not success:
			return err

		node2.append(node4)

		return (success, src6, node2)


	def validate_or(self, src):
		success, src2, node = self.validate_and(src)

		node3 = ["||", node]

		while success and 0 < len(src2):
			if src2[0] != "||":
				break

			success, src3, node2 = (self.
				validate_and(src2[1:]))

			if success:
				node3.append(node2)
				src2 = src3

		if success:
			if 3 <= len(node3):
				node = node3

			return (True, src2, node)
		else:
			return (False, src, "")

	def validate_and(self, src):
		success, src2, node = self.validate_add(src)

		node3 = ["&&", node]

		while success and 0 < len(src2):
			if src2[0] != "&&":
				break

			success, src3, node2 = (self.
				validate_add(src2[1:]))

			if success:
				node3.append(node2)
				src2 = src3

		if success:
			if 3 <= len(node3):
				node = node3

			return (True, src2, node)
		else:
			return (False, src, "")

	def validate_add(self, src):
		success, src2, node = self.validate_mul(src)

		while success and 0 < len(src2):
			if not (src2[0] in ["+", "-"]):
				break

			success, src3, node2 = (self.
				validate_mul(src2[1:]))

			if success:
				node = [src2[0], node, node2]
				src2 = src3

		if success:
			return (True, src2, node)
		else:
			return (False, src, "")


	def validate_mul(self, src):
		success, src2, node = self.validate_call(src)

		while success and 0 < len(src2):
			if not (src2[0] in ["*", "/", "%"]):
				break

			success, src3, node2 = (self.
				validate_call(src2[1:]))

			if success:
				node = [src2[0], node, node2]
				src2 = src3

		if success:
			return (True, src2, node)
		else:
			return (False, src, "")

	def validate_call(self, src):
		success, src2, node = self.validate_value(src)

		if len(src2) == 0:
			return (success, src2, node)

		while 0 < len(src2):
			success, src3, node2 = self.validate_id(src2)

			if not success:
				success = True
				break

			node3 = ["call", node2]
			src2 = src3
			
			if self.typeof_node(node) == "tuple":
				node3 = node3 + [node[1:]]
			else:
				node3.append([node])

			#right params (optional)

			success2, src4, node2 = (
				self.validate_right_param(src2))

			if success2:
				node3 = node3 + [node2]
				src2 = src4

			node = node3

		return (success, src2, node)

	def validate_list_of_id(self, src):
		success, src2, node = self.validate_list(src, accept_list=False)

		if success:
			if self.typeof_node(node) != "tuple":
				success = False
				node = ""

		if success:
			for i in node[1:]:
				if not i.isidentfier():
					success = False
					node = ""
					break

		return (success, src2, node)

	def validate_right_param(self, src):
		success, src2, node = self.validate_list(src, accept_list=False)

		if success and self.typeof_node(node) == "tuple":
			node = [node[1:]]

		success2 = success

		while success2 and 0 < len(src2):
			if not src2[0] in ["and", "or"]:
				break

			nexus = src2[0]

			# id (optional)

			success2, src3, node2 = self.validate_id(src2[1:])

			single_method = not success2

			if not success2:
				src3 = src2[1:]

			# parameters

			success3, src4, node3 = self.validate_list(src3, accept_list=False)

			if not success3 or self.typeof_node(node3) != "tuple":
				if single_method:
					src4 = src3
					node3 = node2
				else:
					break

			node3 = [nexus, node3[1:]]

			if not single_method:
				node3.append(node2)

			src2 = src4
			node = node + [node3]

			if len(src2):
				success2 = True

		return (success, src2, node)

	def validate_list(self, src, accept_tuple=True, accept_list=True):
		rights = []
		lefts = []
		left_by_right = {}
		name_by_right = {}
		if accept_tuple:
			rights.append('(')
			lefts.append(')')
			left_by_right['('] = ')'
			name_by_right['('] = "tuple"
		if accept_list:
			rights.append('[')
			lefts.append(']')
			left_by_right['['] = ']'
			name_by_right['['] = "list"

		err = (False, src, "")

		if len(src) < 2:
			return err
		elif not (src[0] in rights):
			return err

		src2 = src[1:]

		node = [name_by_right[src[0]]]
		right = left_by_right[src[0]]


		if src2[0] == right:
			return (True, src2[1:], node)

		while 0 < len(src2):
			success, src2, node2 = self.validate_expr(src2)

			if not success or len(src2) == 0:
				return err
			elif not (src2[0] in [right, ',']):
				return err

			node.append(node2)

			if src2[0] == right:
				return (success, src2[1:], node)

			src2 = src2[1:]

		return err

	def validate_id(self, src):
		if len(src) == 0:
			return (False, src, "")

		success = (src[0].isidentifier() and
				not (src[0] in self.keyword))

		src2 = src[1:] if success else src

		return (success, src2, src[0])

	def validate_keyword(self, src, keyword=None):
		err = (False, src, "")

		if len(src) == 0:
			return err
		elif (src[0] in self.keyword and
				(keyword == None or src[0] == keyword)):

			return (True, src[1:], src[0])
		else:
			return err

	def validate_num(self, src):
		if len(src) == 0:
			return (False, src, "")

		success = src[0].isdecimal()

		src2 = src[1:] if success else src

		return (success, src2, int(src[0]) if success else src[0])

	def validate_str(self, src):
		if len(src) == 0:
			return (False, src, "")

		success = src[0].startswith('\"')

		src2 = src[1:] if success else src

		return (success, src2, src[0])

	def validate_value(self, src):
		for f in [self.validate_id,
				self.validate_num,
				self.validate_str,
				self.validate_list]:


			success, src2, node = f(src)

			if success:
				return (success, src2, node)

		return (False, src, "")

	def typeof_node(self, node):
		if type(node) == list and 0 < len(node):
			return node[0]
		else:
			return type(node)


if __name__ == "__main__":
	import sys
	import io

	src = """
		stdout putln("Hello, world!")
		"""
	interactive = False

	def builtin_exit():
		global interactive
		interactive = False

		return "bye"

	def builtin_help():
		return """\
			syntax:
			expr = let | ';' expr
			let = 'let' id then (| ',' id then) expr
			then = or 'then' expr ('else' expr)
			or = and '||' (and | or) 
			and = add '&&' (add | and)
			add = (mul | add) ('+' | '-') mul
			mul = (call | mul) ('*' | '/' | '%') call
			call = (val | call | tuple) id (| rparams) 
			rparams = tuple (| rparams2)
			rparams2 = ('and' | 'or') (| id) tuple (| rparams2)
			list = '[' (| vals) ']'
			tuple = '(' (| vals) ')'
			vals = (val | vals) (| ',' val)
			val = id | num | str | tuple | list
			# (x,y)f == x f(y) == () f(x,y)
			# nexus (virtual macro functions for chaining):
			#   and/or-nexus makes short-circuit.
			#   x f(y)and(z) :
			#     (let tmp x; tmp f(y) && tmp f(z))  # if f returns boolean
			#     (let tmp x; [tmp f(y), tmp f(z)])  # if f returns not boolean value
			#   x f(y)and g(z) :
			#     # for params(y,z), uses g instead of f
			#   currently or-nexus requires f to return boolean.
			#   if does not, makes runtime-error because of dynamic-typing.
			funcs:
			()exit; ()help
			(x, y)eq; (x, y)lt; (x, y)gt; (bool)not
			(array, index)ld; (array, index, value)st
			(sequence)len; (sequence, separater)split
			(sequence, start, end)slice; (sequence, separater)join
			(element, sequence)in; (element, sequence)contains
			(element, sequence)index_of; (element, sequence)last_index_of
			()input
			(file, str)put; (file, str)putln
			(file)getln
			""".replace('\t', "")

	def builtin_put(*args):
		if len(args) == 2:
			f = args[0]
			s = args[1]
		else:
			f = sys.stdout
			s = args[0]

		return f.write(s)

	def builtin_putln(*args):
		if len(args) == 2:
			f = args[0]
			s = args[1]
		else:
			f = sys.stdout
			s = args[0]

		return f.write(s + "\n")

	def builtin_getln(*args):
		if len(args) == 1:
			f = args[0]
		else:
			f = sys.stdin

		return f.readline().replace("\n", "")

	if 1 < len(sys.argv):
		if sys.argv[1] == '-i':
			interactive = True
		else:
			with io.open(sys.argv[1]) as f:
				src = f.read()

	native_funcs = {
		'input': input,
		'put': builtin_put,
		'putln': builtin_putln,
		'getln': builtin_getln}
	with_vars = {
		'stdin': sys.stdin,
		'stdout': sys.stdout,
		'stderr': sys.stderr,
		'args': sys.argv[2:]}


	if interactive:
		native_funcs['exit'] = builtin_exit
		native_funcs['help'] = builtin_help

		chi = Pych(native_funcs, with_vars)

		sys.stdout.write('>')
		src = input().strip()
		while interactive:
			if src == ";;":
				src = ""
				break

			if chi.load(src)[0]:
				try:
					print(chi.eval(src))
				except Exception:
					print("error")
				src = ""
				sys.stdout.write('>')
			else:
				src = src + (" " if src != ";" else "")
				sys.stdout.write(' ')

			if interactive:
				src = src + input().strip()
	else:
		chi = Pych(native_funcs, with_vars)
		r = chi.eval(src)


"""Minimal S-expression reader/writer for KiCad files."""
import uuid as _uuid

class Sym(str):
    """Bare (unquoted) symbol token."""
    __slots__ = ()
    def __repr__(self): return f"Sym({str.__repr__(self)})"

def parse(text):
    i, n = 0, len(text)
    stack = [[]]
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c == '(':
            stack.append([]); i += 1
        elif c == ')':
            lst = stack.pop(); stack[-1].append(lst); i += 1
        elif c == '"':
            j = i + 1; buf = []
            while text[j] != '"':
                if text[j] == '\\':
                    buf.append(text[j:j+2]); j += 2
                else:
                    buf.append(text[j]); j += 1
            stack[-1].append(''.join(buf).replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')); i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            tok = text[i:j]
            try:
                v = int(tok)
            except ValueError:
                try:
                    v = float(tok)
                except ValueError:
                    v = Sym(tok)
            stack[-1].append(v); i = j
    return stack[0]

def _fmt_num(v):
    if isinstance(v, bool):
        return 'yes' if v else 'no'
    if isinstance(v, int):
        return str(v)
    s = f"{v:.6f}".rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'

def dumps(node, indent=0):
    if isinstance(node, list):
        if not node:
            return '()'
        head = node[0]
        parts = []
        simple = all(not isinstance(x, list) for x in node)
        if simple:
            return '(' + ' '.join(dumps(x) for x in node) + ')'
        out = '(' + dumps(head)
        i = 1
        # keep leading atoms on the same line
        while i < len(node) and not isinstance(node[i], list):
            out += ' ' + dumps(node[i]); i += 1
        for x in node[i:]:
            out += '\n' + '\t' * (indent + 1) + dumps(x, indent + 1)
        out += '\n' + '\t' * indent + ')'
        return out
    if isinstance(node, Sym):
        return str(node)
    if isinstance(node, str):
        return '"' + node.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    return _fmt_num(node)

def find(node, key):
    """First child list whose head == key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None

def findall(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]

def new_uuid():
    return str(_uuid.uuid4())

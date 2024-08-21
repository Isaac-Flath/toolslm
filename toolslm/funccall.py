# AUTOGENERATED! DO NOT EDIT! File to edit: ../01_funccall.ipynb.

# %% auto 0
__all__ = ['empty', 'get_schema', 'python']

# %% ../01_funccall.ipynb 2
import inspect
from fastcore.utils import *
from fastcore.docments import docments

# %% ../01_funccall.ipynb 3
empty = inspect.Parameter.empty

# %% ../01_funccall.ipynb 11
def _types(t:type)->tuple[str,Optional[str]]:
    "Tuple of json schema type name and (if appropriate) array item name."
    if t is empty: raise TypeError('Missing type')
    tmap = {int:"integer", float:"number", str:"string", bool:"boolean", list:"array", dict:"object"}
    tmap.update({k.__name__: v for k, v in tmap.items()})
    if getattr(t, '__origin__', None) in  (list,tuple): return "array", tmap.get(t.__args__[0], "object")
    else: return tmap[t], None

# %% ../01_funccall.ipynb 14
def _param(name, info):
    "json schema parameter given `name` and `info` from docments full dict."
    paramt,itemt = _types(info.anno)
    pschema = dict(type=paramt, description=info.docment or "")
    if itemt: pschema["items"] = {"type": itemt}
    if info.default is not empty: pschema["default"] = info.default
    return pschema

# %% ../01_funccall.ipynb 17
def get_schema(f:callable, pname='input_schema')->dict:
    "Convert function `f` into a JSON schema `dict` for tool use."
    d = docments(f, full=True)
    ret = d.pop('return')
    d.pop('self', None) # Ignore `self` for methods
    paramd = {
        'type': "object",
        'properties': {n:_param(n,o) for n,o in d.items() if n[0]!='_'},
        'required': [n for n,o in d.items() if o.default is empty and n[0]!='_']
    }
    desc = f.__doc__
    assert desc, "Docstring missing!"
    if ret.anno is not empty: desc += f'\n\nReturns:\n- type: {_types(ret.anno)[0]}'
    if ret.docment: desc += f'\n- description: {ret.docment}'
    return {'name':f.__name__, 'description':desc, pname:paramd}

# %% ../01_funccall.ipynb 24
import ast, time, signal, traceback
from fastcore.utils import *

# %% ../01_funccall.ipynb 25
def _copy_loc(new, orig):
    "Copy location information from original node to new node and all children."
    new = ast.copy_location(new, orig)
    for field, o in ast.iter_fields(new):
        if isinstance(o, ast.AST): setattr(new, field, _copy_loc(o, orig))
        elif isinstance(o, list): setattr(new, field, [_copy_loc(value, orig) for value in o])
    return new

# %% ../01_funccall.ipynb 27
def _run(code:str ):
    "Run `code`, returning final expression (similar to IPython)"
    tree = ast.parse(code)
    last_node = tree.body[-1] if tree.body else None
    
    # If the last node is an expression, modify the AST to capture the result
    if isinstance(last_node, ast.Expr):
        tgt = [ast.Name(id='_result', ctx=ast.Store())]
        assign_node = ast.Assign(targets=tgt, value=last_node.value)
        tree.body[-1] = _copy_loc(assign_node, last_node)

    compiled_code = compile(tree, filename='<ast>', mode='exec')
    namespace = {}
    stdout_buffer = io.StringIO()
    saved_stdout = sys.stdout
    sys.stdout = stdout_buffer
    try: exec(compiled_code, namespace)
    finally: sys.stdout = saved_stdout
    _result = namespace.get('_result', None)
    if _result is not None: return _result
    return stdout_buffer.getvalue().strip()

# %% ../01_funccall.ipynb 32
def python(code, # Code to execute
           timeout=5 # Maximum run time in seconds before a `TimeoutError` is raised
          ): # Result of last node, if it's an expression, or `None` otherwise
    """Executes python `code` with `timeout` and returning final expression (similar to IPython).
    Raised exceptions are returned as a string, with a stack trace."""
    def handler(*args): raise TimeoutError()
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try: return _run(code)
    except Exception as e: return traceback.format_exc()
    finally: signal.alarm(0)

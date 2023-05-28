""" Runtime functions from the PyYC runtime library. 

    These functions allow us to reference the runtime library wihtout errors
"""

import ast

class PyObj(ast.expr):
    """ A PYOBJ is an AST node which represents a boxed pointer.

        It is used to represent any Python object in the runtime library.
        In memory, it is a pointer to a struct which contains the type tag:
        0b00 - int
        0b01 - bool
        # 0b10 - float
        0b11 - big
    """
    ...

class Big_PyObj_P(ast.expr):
    """ A Big_PyObj_P is an AST node which represents a pointer to an unboxed
        big_pyobj struct.
    """
    ...

class Int(ast.expr):
    """ An Int is an AST node which represents an unboxed int. """
    ...

class Bool(ast.expr):
    """ A Bool is an AST node which represents an unboxed bool. """
    ...

# class CallRuntime(ast.Call):
#     """ A CallRuntime is an AST node which represents a call to a runtime
#         function. It is used to ensure that the runtime functions are
#         referenced correctly.
#     """
#     ...

def is_int(val: PyObj) -> Bool:
    return ast.Call(func=ast.Name(id="is_int", ctx=ast.Load()), args=[val], keywords=[])
    # return CallRuntime(func=ast.Name(id="is_int", ctx=ast.Load()), args=[val])
    # return ast.parse(f"is_int({val})").body[0].value

def is_bool(val: PyObj) -> Bool:
    return ast.Call(func=ast.Name(id="is_bool", ctx=ast.Load()), args=[val], keywords=[])
    # return CallRuntime(func=ast.Name(id="is_bool", ctx=ast.Load()), args=[val])
    # return ast.parse(f"is_bool({val})").body[0].value

def is_big(val: PyObj) -> Bool:
    return ast.Call(func=ast.Name(id="is_big", ctx=ast.Load()), args=[val], keywords=[])
    # return CallRuntime(func=ast.Name(id="is_big", ctx=ast.Load()), args=[val])
    # return ast.parse(f"is_big({val})").body[0].value

def inject_int(i: ast.Constant) -> PyObj:
    return ast.Call(func=ast.Name(id="inject_int", ctx=ast.Load()), args=[i], keywords=[])
    # return CallRuntime(func=ast.Name(id="inject_int", ctx=ast.Load()), args=[i])
    # return ast.parse(f"inject_int({i})").body[0].value

def inject_bool(b: ast.Constant) -> PyObj:
    return ast.Call(func=ast.Name(id="inject_bool", ctx=ast.Load()), args=[b], keywords=[])
    # return CallRuntime(func=ast.Name(id="inject_bool", ctx=ast.Load()), args=[b])
        # return CallRuntime(func=ast.Name(id="inject_bool", ctx=ast.Load()), args=[b])
    # # return CallRuntime(func=ast.Name(id="inject_bool", ctx=ast.Load()), args=[b])
    # return ast.parse(f"inject_bool({b})").body[0].value

def inject_big(p: Big_PyObj_P) -> PyObj:
    return ast.Call(func=ast.Name(id="inject_big", ctx=ast.Load()), args=[p], keywords=[])
    # return CallRuntime(func=ast.Name(id="inject_big", ctx=ast.Load()), args=[p])
        # return CallRuntime(func=ast.Name(id="inject_big", ctx=ast.Load()), args=[p])
    # # return CallRuntime(func=ast.Name(id="inject_big", ctx=ast.Load()), args=[p])
    # return ast.parse(f"inject_big({p})").body[0].value

def project_int(val: PyObj) -> Int:
    return ast.Call(func=ast.Name(id="project_int", ctx=ast.Load()), args=[val], keywords=[])
    # return CallRuntime(func=ast.Name(id="project_int", ctx=ast.Load()), args=[val])
    # return ast.parse(f"project_int({val})").body[0]

def project_bool(val: PyObj) -> Bool:
    return ast.Call(func=ast.Name(id="project_bool", ctx=ast.Load()), args=[val], keywords=[])
    # return CallRuntime(func=ast.Name(id="project_bool", ctx=ast.Load()), args=[val])
    # return ast.parse(f"project_bool({val})").body[0]

def project_big(val: PyObj) -> Big_PyObj_P:
    return ast.Call(func=ast.Name(id="project_big", ctx=ast.Load()), args=[val], keywords=[])
    # return CallRuntime(func=ast.Name(id="project_big", ctx=ast.Load()), args=[val])
    # return ast.parse(f"project_big({val})").body[0]

"""
int is_true(pyobj v);
void print_any(pyobj p);
pyobj input_int();
pyobj input_pyobj();
pyobj eval_pyobj(pyobj x);
pyobj eval_input_pyobj();

big_pyobj* create_list(pyobj length);
big_pyobj* create_dict();
pyobj set_subscript(pyobj c, pyobj key, pyobj val);
pyobj get_subscript(pyobj c, pyobj key);
"""
def is_true(val: PyObj) -> Int:
    return ast.Call(func=ast.Name(id="is_true", ctx=ast.Load()), args=[val], keywords=[])
    # return ast.parse(f"is_true({val})").body[0]

# def print_any(val: PyObj) -> CallRuntime:
def print_any(val: PyObj) -> ast.Call:
    return
    # return ast.parse(f"print_any({val})").body[0]

# def input_int() -> pyobj:
#     return ast.parse(f"input_int()").body[0].value

# def input_pyobj() -> pyobj:
#     return ast.parse(f"input_pyobj()").body[0].value

# def eval_pyobj(val: pyobj) -> pyobj:
#     return ast.parse(f"eval_pyobj({val})").body[0].value

def eval_input_pyobj() -> PyObj:
        # return CallRuntime(func=ast.Name(id="eval_input_pyobj", ctx=ast.Load()), args=[])
    # # return CallRuntime(func=ast.Name(id="eval_input_pyobj", ctx=ast.Load()), args=[])
    # return ast.parse(f"eval_input_pyobj()").body[0].value
    return ast.Call(func=ast.Name(id="eval_input_pyobj", ctx=ast.Load()), args=[], keywords=[])
    # return CallRuntime(func=ast.Name(id="eval_input_pyobj", ctx=ast.Load()), args=[])

def create_list(length: PyObj) -> Big_PyObj_P:
    return ast.Call(func=ast.Name(id="create_list", ctx=ast.Load()), args=[length], keywords=[])
    # return CallRuntime(func=ast.Name(id="create_list", ctx=ast.Load()), args=[length])
    # return ast.parse(f"create_list({length})").body[0].value

def create_dict() -> Big_PyObj_P:
    return ast.Call(func=ast.Name(id="create_dict", ctx=ast.Load()), args=[], keywords=[])
    # return CallRuntime(func=ast.Name(id="create_dict", ctx=ast.Load()), args=[])
    # return ast.parse(f"create_dict()").body[0].value

def set_subscript(c: Big_PyObj_P, key: PyObj, val: PyObj) -> PyObj:
    return ast.Call(func=ast.Name(id="set_subscript", ctx=ast.Load()), args=[c, key, val], keywords=[])
    # return CallRuntime(func=ast.Name(id="set_subscript", ctx=ast.Load()), args=[c, key, val])
    # return ast.parse(f"set_subscript({c}, {key}, {val})").body[0].value

def get_subscript(c: Big_PyObj_P, key: PyObj) -> PyObj:
    return ast.Call(func=ast.Name(id="get_subscript", ctx=ast.Load()), args=[c, key], keywords=[])
    # return CallRuntime(func=ast.Name(id="get_subscript", ctx=ast.Load()), args=[c, key])
    # return ast.parse(f"get_subscript({c}, {key})").body[0].value

def add(a: Big_PyObj_P, b: Big_PyObj_P) -> Big_PyObj_P:
    return ast.Call(func=ast.Name(id="add", ctx=ast.Load()), args=[a, b], keywords=[])
    # return CallRuntime(func=ast.Name(id="add", ctx=ast.Load()), args=[a, b])
    # return ast.parse(f"add({a}, {b})").body[0].value

def equal(a: Big_PyObj_P, b: Big_PyObj_P) -> Int:
    return ast.Call(func=ast.Name(id="equal", ctx=ast.Load()), args=[a, b], keywords=[])
    # return CallRuntime(func=ast.Name(id="equal", ctx=ast.Load()), args=[a, b])
    # return ast.parse(f"equal({a}, {b})").body[0].value

def error_pyobj() -> PyObj:
    return ast.Call(func=ast.Name(id="error_pyobj", ctx=ast.Load()), args=[ast.Constant(0)], keywords=[])

"""
int is_int(pyobj val);
int is_bool(pyobj val);
int is_big(pyobj val);
int is_function(pyobj val);
int is_object(pyobj val);
int is_class(pyobj val);
int is_unbound_method(pyobj val);
int is_bound_method(pyobj val);

pyobj inject_int(int i);
pyobj inject_bool(int b);
pyobj inject_big(big_pyobj* p);

int project_int(pyobj val);
int project_bool(pyobj val);
big_pyobj* project_big(pyobj val);

/* Operations */

int is_true(pyobj v);
void print_any(pyobj p);
pyobj input_int();
pyobj input_pyobj();
pyobj eval_pyobj(pyobj x);
pyobj eval_input_pyobj();

big_pyobj* create_list(pyobj length);
big_pyobj* create_dict();
pyobj set_subscript(pyobj c, pyobj key, pyobj val);
pyobj get_subscript(pyobj c, pyobj key);

big_pyobj* add(big_pyobj* a, big_pyobj* b);
int equal(big_pyobj* a, big_pyobj* b);
int not_equal(big_pyobj* x, big_pyobj* y);

pyobj error_pyobj(char* string);
"""

# Custom
def inject_constant(val: ast.Constant):
    if isinstance(val.value, bool):
        return inject_bool(val)
    elif isinstance(val.value, int):
        return inject_int(val)
    else:
        raise Exception(f"Cannot inject {type(val)}")

def error_handler():
    return error_pyobj()


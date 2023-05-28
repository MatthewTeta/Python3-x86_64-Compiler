''' These functions are to be read by inspect and AST to extend the runtime. '''
from pyyc_runtime import *

def __int__(value: PyObj):
    if is_int(value):
        target = value
    elif is_bool(value):
        target = project_bool(value)
        target = inject_int(target)
    else:
        error_pyobj()
    return target

def __not__(value: PyObj):
    if is_bool(value):
        target = value ^ 4
    elif is_int(value):
        target = project_int(value) == 0
        target = inject_bool(target)
    elif is_big(value):
        target = inject_bool(is_true(value) ^ 1)
    return target

def __add__(left: PyObj, right: PyObj):
    target = 0
    if is_int(left):
        left = project_int(left)
        if is_int(right):
            right = project_int(right)
            target = left + right
            target = inject_int(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left + right
            target = inject_int(target)
        elif is_big(left):
            error_pyobj()
    elif is_bool(left):
        left = project_bool(left)
        if is_int(right):
            right = project_int(right)
            target = left + right
            target = inject_int(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left + right
            target = inject_int(target)
        elif is_big(left):
            error_pyobj()
    elif is_big(left):
        if is_int(right):
            error_pyobj()
        elif is_bool(right):
            error_pyobj()
        elif is_big(right):
            left = project_big(left)
            right = project_big(right)
            target = inject_big(add(left, right))
    return target

def __neg__(value: PyObj):
    target = 0
    if is_int(value):
        value = project_int(value)
        target = -value
        target = inject_int(target)
    elif is_bool(value):
        value = project_bool(value)
        target = -value
        target = inject_int(target)
    elif is_big(value):
        error_pyobj()
    return target

def __eq__(left: PyObj, right: PyObj):
    target = 0
    if is_int(left):
        left = project_int(left)
        if is_int(right):
            right = project_int(right)
            target = left == right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left == right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_bool(left):
        left = project_bool(left)
        if is_int(right):
            right = project_int(right)
            target = left == right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left == right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_big(left):
        if is_int(right):
            error_pyobj()
        elif is_bool(right):
            error_pyobj()
        elif is_big(right):
            left = project_big(left)
            right = project_big(right)
            target = inject_bool(equal(left, right))
    return target

def __ne__(left: PyObj, right: PyObj):
    target = 0
    if is_int(left):
        left = project_int(left)
        if is_int(right):
            right = project_int(right)
            target = left != right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left != right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_bool(left):
        left = project_bool(left)
        if is_int(right):
            right = project_int(right)
            target = left != right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left != right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_big(left):
        if is_int(right):
            error_pyobj()
        elif is_bool(right):
            error_pyobj()
        elif is_big(right):
            left = project_big(left)
            right = project_big(right)
            target = inject_bool(equal(left, right) ^ 1)
    return target

def __lt__(left: PyObj, right: PyObj):
    target = 0
    if is_int(left):
        left = project_int(left)
        if is_int(right):
            right = project_int(right)
            target = left < right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left < right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_bool(left):
        left = project_bool(left)
        if is_int(right):
            right = project_int(right)
            target = left < right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left < right
            target = inject_bool(target)
    return target

def __le__(left: PyObj, right: PyObj):
    target = 0
    if is_int(left):
        left = project_int(left)
        if is_int(right):
            right = project_int(right)
            target = left <= right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left <= right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_bool(left):
        left = project_bool(left)
        if is_int(right):
            right = project_int(right)
            target = left <= right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left <= right
            target = inject_bool(target)
    return target

def __gt__(left: PyObj, right: PyObj):
    target = 0
    if is_int(left):
        left = project_int(left)
        if is_int(right):
            right = project_int(right)
            target = left > right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left > right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_bool(left):
        left = project_bool(left)
        if is_int(right):
            right = project_int(right)
            target = left > right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left > right
            target = inject_bool(target)
    return target

def __ge__(left: PyObj, right: PyObj):
    target = 0
    if is_int(left):
        left = project_int(left)
        if is_int(right):
            right = project_int(right)
            target = left >= right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left >= right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_bool(left):
        left = project_bool(left)
        if is_int(right):
            right = project_int(right)
            target = left >= right
            target = inject_bool(target)
        elif is_bool(right):
            right = project_bool(right)
            target = left >= right
            target = inject_bool(target)
        elif is_big(right):
            error_pyobj()
    elif is_big(left):
        error_pyobj()
    return target

def __is__(left: PyObj, right: PyObj):
    # Direct object identity check
    return left == right

def cmp(op: ast.cmpop):
    return {
        'Eq': __eq__,
        'NotEq': __ne__,
        'Lt': __lt__,
        'LtE': __le__,
        'Gt': __gt__,
        'GtE': __ge__,
        'Is': __is__,
    }[op.__class__.__name__]

PYTHON_RUNTIME_FAKE_HEADER = """
class PyObj: ...
class Big_PyObj_P: ...
def is_int(x: PyObj) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)
def is_bool(x: PyObj) -> bool:
    return isinstance(x, bool)
def is_big(x: PyObj) -> bool:
    return not is_int(x) and not is_bool(x)
def project_int(x: PyObj) -> int:
    return x
def project_bool(x: PyObj) -> bool:
    return x
def project_big(x: PyObj) -> Big_PyObj_P:
    return x
def inject_int(x: int) -> PyObj:
    return x
def inject_bool(x: bool) -> PyObj:
    return x
def inject_big(x: Big_PyObj_P) -> PyObj:
    return x
def is_true(x: PyObj) -> bool:
    return bool(x)
def error_pyobj():
    raise TypeError("Invalid type")
def eval_input_pyobj() -> PyObj:
    return eval(input())
def print_any(x: PyObj):
    print(x)
def add(x: Big_PyObj_P, y: Big_PyObj_P) -> Big_PyObj_P:
    return x + y
def equal(x: Big_PyObj_P, y: Big_PyObj_P) -> Big_PyObj_P:
    return x == y
def create_list(len: PyObj) -> Big_PyObj_P:
    return [0] * len
def create_dict() -> Big_PyObj_P:
    return {}
def set_subscript(c: PyObj, key: PyObj, value: PyObj) -> PyObj:
    c[key] = value
    return c
def get_subscript(c: PyObj, key: PyObj) -> PyObj:
    return c[key]



"""

# def __add__(target: PyObj, left: PyObj, right: PyObj):
#     if is_int(left):
#         left = project_int(left)
#         if is_int(right):
#             right = project_int(right)
#             target = left + right
#             right = inject_int(right)
#             target = inject_int(target)
#         elif is_bool(right):
#             right = project_bool(right)
#             target = left + right
#             right = inject_bool(right)
#             target = inject_int(target)
#         left = inject_int(left)
#     elif is_bool(left):
#         left = project_bool(left)
#         if is_int(right):
#             right = project_int(right)
#             target = left + right
#             right = inject_int(right)
#             target = inject_int(target)
#         elif is_bool(right):
#             right = project_bool(right)
#             target = left + right
#             right = inject_bool(right)
#             target = inject_int(target)
#         left = inject_bool(left)
#     return target
# ...


# def explicate_op(c, a, b, op):
    # c = a op b
    # a and b and c are of type pyobj
    # Cases:
    # int + int
    # int + bool
    # int + big
    #   int + dict
    #   int + list
    # bool + int
    # bool + bool
    # bool + big
    #   bool + dict
    #   bool + list
    # big + int
    #   dict + int
    #   list + int
    # big + bool
    #   dict + bool
    #   list + bool
    # big + big
    #   dict + big
    #       dict + dict
    #       dict + list
    #   list + big
    #       list + dict
    #       list + list
    # def wrapper(c, a, b):
    #     if is_int(a):
    #         a = project_int(a)
    #         if is_int(b):
    #             b = project_int(b)
    #             c = a + b
    #             b = inject_int(b)
    #             c = inject_int(c)
    #         elif is_bool(b):
    #             b = project_bool(b)
    #             c = a + b
    #             b = inject_bool(b)
    #             c = inject_int(c)
    #         elif is_big(b):
    #             # This is an error
    #             pass
    #         a = inject_int(a)
    #     elif is_bool(a):
    #         a = project_bool(a)
    #         if is_int(b):
    #             b = project_bool(b)
    #             c = a + b
    #             b = inject_bool(b)
    #             c = inject_int(c)
    #         elif is_bool(b):
    #             b = project_bool(b)
    #             c = a + b
    #             b = inject_bool(b)
    #             c = inject_bool(c)
    #         elif is_big(b):
    #             # This is an error
    #             pass
    #         a = inject_bool(a)
    #     elif is_big(a):
    #         a = project_big(a)
    #         if is_int(b):
    #             # This is an error
    #             pass
    #         elif is_bool(b):
    #             # This is an error
    #             pass
    #         elif is_big(b):
    #             b = project_big(b)
    #             add(a, b)
    #             b = inject_big(b)
    #         a = project_big(b)
    # return wrapper

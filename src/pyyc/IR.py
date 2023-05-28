'''
Define the IR types and print function.
'''

import sys
import ast
from io import StringIO
from typing import ClassVar, List, MutableSet, Union, Tuple

TAB_PREF = '    '

# Begin IR Types

# IR Tree Structure (everything inherits from IR)
class IR(ast.AST):
    _attributes: ClassVar[Tuple[str, ...]] = ()
    _fields: ClassVar[Tuple[str, ...]]
    def __init__(self, *args, **kwargs):
        # TODO: check that all fields are set and assigned to proper types
        for i, key in enumerate(args):
            setattr(self, self._fields[i], key)
        for key, value in kwargs.items():
            setattr(self, key, value)
        for key in self._fields:
            if not hasattr(self, key):
                raise ValueError(f'Field "{key}" not set on new {self.__class__.__name__}')
            else:
                # Check type of assignment
                ...
    def __str__(self):
        return self.__class__.__name__
    # def __repr__(self) -> str:
    #     return self.__class__.__name__

# Data Types
class ir_type(type):
    def __str__(self):
        return self.__name__
    # def __repr__(self):
    #     return self.__name__

class ir_void(metaclass=ir_type): ...
class ir_int(metaclass=ir_type): ...
class ir_bool(metaclass=ir_type): ...
class ir_pyobj(metaclass=ir_type): ...
class ir_big(metaclass=ir_type): ...
class ir_big_list(ir_big): ...
class ir_big_dict(ir_big): ...

# IR Tree
class ir_mod(IR): ...
class ir_Module(ir_mod):
    _fields = ('functions',)
    functions: MutableSet['ir_fnct']
    # TODO: add .rodata

class ir_fnct(IR): ...
class ir_Function(ir_fnct):
    _fields = ('name', 'args', 'body', 'return_type', 'variables',)
    name: str
    args: List['ir_trgt']
    body: List['ir_stmt']
    return_type: 'ir_type'
    variables: MutableSet['ir_trgt']
    register_assignments: dict['arg', 'reg']
    def update_variables(self):
        # Update the dict of variables
        self.variables = set()
        for stmnt in ast.walk(self):
            if isinstance(stmnt, ir_Name):
                self.variables.add(stmnt.id)

class ir_stmt(IR): ...
class ir_Assign(ir_stmt):
    '''
    - x = y
    - x = y + 2
    - x = y + z
    - x = y > z
    - x = f(y, z)
    '''
    _fields = ('target', 'value',)
    target: 'ir_trgt'
    value: 'ir_expr'
class ir_Expr(ir_stmt):
    '''
    - f()
    - f(x, y)
    - x > 2
    - y + 2
    '''
    _fields = ('value',)
    value: 'ir_expr'
class ir_Label(ir_stmt):
    _fields = ('name',)
    name: str
class ir_Return(ir_stmt):
    '''
    - return x
    - return
    '''
    _fields = ('value',)
    value: Union['ir_trgt', None]
class ir_cntrl(ir_stmt): ...
class ir_Jump(ir_cntrl):
    _fields = ('label',)
    label: str
class ir_Branch(ir_cntrl):
    _fields = ('condition', 'true_label', 'false_label',)
    condition: 'ir_trgt'
    true_label: str
    false_label: str


class ir_trgt(IR): ...
class ir_Name(ir_trgt):
    '''
    - x
    - y
    - z
    '''
    _fields = ('id', 'type',)
    id: str
    type: 'ir_type' = ir_void
    def __str__(self):
        # print("\n\n__STR__: " + self.__class__.__name__ + "\n\n")
        return self.id
    def __repr__(self):
        # print("\n\n__REPR__: " + self.__class__.__name__ + "\n\n")
        return self.id
class ir_Constant(ir_trgt):
    '''
    - 2
    - 3
    - True
    - False
    '''
    _fields = ('value', 'type',)
    value: Union[int, bool]
    type: Union[ir_int, ir_bool]
    def __str__(self):
        # print("\n\n__STR__: " + self.__class__.__name__ + "\n\n")
        return f'${str(self.value)}'
    def __repr__(self):
        # print("\n\n__REPR__: " + self.__class__.__name__ + "\n\n")
        return f'${str(self.value)}'

class ir_expr(IR): ...
class ir_Target(ir_expr):
    '''
    - x
    - y
    - z
    '''
    _fields = ('target',)
    target: ir_trgt
class ir_Call(ir_expr):
    '''
    - f()
    - f(x, y)
    - f(x, y, z)
    - f(x, y, z, w)
    '''
    _fields = ('func', 'args',)
    func: str
    args: List['ir_trgt']
class ir_UnaryOp(ir_expr):
    '''
    - not x
    - -x
    '''
    _fields = ('op', 'operand',)
    op: 'ir_unaryop'
    operand: ir_trgt
class ir_BinOp(ir_expr):
    '''
    - x + y
    - x + 2
    '''
    _fields = ('left', 'op', 'right',)
    left: ir_trgt
    op: 'ir_operator'
    right: ir_trgt
class ir_Compare(ir_expr):
    '''
    - x > y
    - x < y
    - x == y
    - x != y
    - x >= y
    - x <= y
    - x is y
    '''
    _fields = ('left', 'op', 'right',)
    left: ir_trgt
    op: 'cmpop'
    right: ir_trgt

class ir_unaryop(IR): ...
class ir_Not(ir_unaryop): ...
class ir_USub(ir_unaryop): ...
unaryops = {
    "ir_Not": "not ",
    "ir_USub": "-",
}

class ir_operator(IR): ...
class ir_Add(ir_operator): ...
class ir_BitXor(ir_operator): ...
binops = {
    "ir_Add": "+",
    "ir_BitXor": "^",
}

class cmpop(IR): ...
class ir_Eq(cmpop): ...
class ir_NotEq(cmpop): ...
class ir_Gt(cmpop): ...
class ir_GtE(cmpop): ...
class ir_Lt(cmpop): ...
class ir_LtE(cmpop): ...
cmpops = {
    "ir_Eq": "==",
    "ir_NotEq": "!=",
    "ir_Lt": "<",
    "ir_LtE": "<=",
    "ir_Gt": ">",
    "ir_GtE": ">=",
}

# End IR Types

def verify_ir(ir: IR):
    # TODO: Verify IR - add more cases
    # for now just check that all ir_cntrl statements are followed by a label
    class VerifyIRVisitor(ast.NodeVisitor):
        def visit_ir_Function(self, node: ir_fnct):
            assert(isinstance(node, ir_Function))
            assert(isinstance(node.name, str))
            assert(isinstance(node.args, list))
            assert(isinstance(node.body, list))
            assert(isinstance(node.return_type, ir_type))
            assert(isinstance(node.variables, set))
            self.generic_visit(node)
            for i, stmnt in enumerate(node.body):
                if isinstance(stmnt, ir_cntrl):
                    if i + 1 >= len(node.body) or not isinstance(node.body[i + 1], ir_Label):
                        val = node.body[i + 1] if i + 1 < len(node.body) else None
                        raise Exception(f"Expected label after control statement, got {val}")

        ...
    
    VerifyIRVisitor().visit(ir)

def print_ir(ir: IR, file: StringIO = sys.stdout, indent: str = '', width: int = 40):
    if not isinstance(ir, IR):
        raise Exception(f"Expected IR, got {ir}")
    # comment_padding = width
    if isinstance(ir, ir_mod):
        for function in ir.functions:
            print_ir(function, file, indent)
        file.write('\n')
    elif isinstance(ir, ir_fnct):
        s = f'{indent}{ir.name}:'
        file.write(s)
        # comment_padding -= len(s)
        # file.write(f"{' ' * comment_padding}; -> {ir.return_type}")
        file.write('\n')
        for arg in ir.args:
            file.write(f'{indent + TAB_PREF}# {arg.id}: {arg.type}\n')
        for s in ir.body:
            if not isinstance(s, ir_stmt):
                raise Exception(f"Expected ir_stmnt, got {s}")
            print_ir(s, file, indent + TAB_PREF)
    elif isinstance(ir, ir_stmt):
        file.write(f'{indent}')
        if isinstance(ir, ir_Assign):
            print_ir(ir.target, file, '')
            file.write(' = ')
            print_ir(ir.value, file, indent + TAB_PREF)
        elif isinstance(ir, ir_Expr):
            # file.write(indent)
            print_ir(ir.value, file, indent + TAB_PREF)
            ...
        elif isinstance(ir, ir_Branch):
            file.write(f'if ')
            print_ir(ir.condition, file, '')
            file.write(f' then {ir.true_label} else {ir.false_label}')
        elif isinstance(ir, ir_Jump):
            file.write(f'goto {ir.label}')
        elif isinstance(ir, ir_Label):
            file.write(f'{ir.name}:')
        elif isinstance(ir, ir_Return):
            file.write(f'return ')
            if ir.value:
                print_ir(ir.value, file, '')
        else:
            # raise Exception(f"Unknown ir_stmnt: {ir.__repr__()}")
            file.write(f'{ir.__class__.__name__}(')
            for i, field in enumerate(ir._fields):
                file.write(f'{field} = {getattr(ir, field)}')
                if i + 1 < len(ir._fields):
                    file.write(', ')
            file.write(')')
            # print_ir(ir, file, indent + TAB_PREF)
        file.write('\n')
    elif isinstance(ir, ir_expr):
        if isinstance(ir, ir_Target):
            print_ir(ir.target, file, '')
        elif isinstance(ir, ir_UnaryOp):
            file.write(f'{unaryops[ir.op.__class__.__name__]}')
            print_ir(ir.operand, file, '')
        elif isinstance(ir, ir_BinOp):
            print_ir(ir.left, file, '')
            file.write(f' {binops[ir.op.__class__.__name__]} ')
            print_ir(ir.right, file, '')
        elif isinstance(ir, ir_Compare):
            print_ir(ir.left, file, '')
            file.write(f' {cmpops[ir.op.__class__.__name__]} ')
            print_ir(ir.right, file, '')
        elif isinstance(ir, ir_Call):
            file.write(f'{ir.func}(')
            for i, arg in enumerate(ir.args):
                print_ir(arg, file, '')
                if i < len(ir.args) - 1:
                    file.write(', ')
            file.write(')')
        else:
            file.write(f'{ir}(\n')
            for i, field in enumerate(ir._fields):
                file.write(f'{indent}{field} <- ')
                print_ir(getattr(ir, field), file, '')
                if i < len(ir._fields) - 1:
                    file.write('\n')
            file.write(f')')
    else:
        file.write(f'{ir}')

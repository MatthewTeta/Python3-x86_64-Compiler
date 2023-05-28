'''
Helpers for P1
'''

from ast import *

from tree_utils import *

# TODO: Break this up into a list for each type of AST node
supported_AST_nodes = [
    Module,
    Assign,
    Expr,
    If,
    IfExp,
    While,
    BoolOp,
    And,
    Or,
    BinOp,
    Add,
    UnaryOp,
    Not,
    USub,
    Compare,
    Eq,
    NotEq,
    Lt,
    LtE,
    Gt,
    GtE,
    Is,
    IsNot,
    In,
    NotIn,
    Call,
    Name,
    Load,
    Store,
    Constant,
    Subscript,
    List,
    Dict,
    Break,
    FunctionDef,
    arguments,
    arg,
    Return,
]

# supported_BinOps = [
#     Add,
# ]

# supported_UnaryOps = [
#     Not,
#     USub,
# ]

def isInputInsideEval(node):
    if isinstance(node, Call):
        if node.func.id == 'input':
            if isinstance(node.parent, Call):
                if node.parent.func.id == 'eval':
                    return True
    return False

class EnsureValid(BodyStacker):
    ''' Ensure that the AST is valid for P1
    '''

    def visit(self, node):
        if type(node) not in supported_AST_nodes:
            raise Exception("Unsupported AST node: " + str(type(node)))
        return super().visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            raise Exception("String constants not supported")
        elif isinstance(node.value, int):
            # Check that we can represent the int with 62 bits
            # using 2's complement
            # if node.value > (2 ** 62 - 1) or node.value < -2**62:
            #     raise Exception("Integer too large for architecture")
            # TODO: Check that the int is in the range of a 62 bit 2's complement
            ...
        return node
    
    def visit_Call(self, node):
        # Check that we're only calling input inside eval
        if node.func.id == 'input':
            if not isInputInsideEval(node):
                raise Exception("input() can only be called inside eval()")
        return node

    def visit_Assign(self, node):
        # Check that we're not assigning to a builtin
        if isinstance(node.targets[0], Name):
            if isBuiltin(node.targets[0].id):
                raise Exception("Cannot assign to builtin in P1")
        return node

    ...

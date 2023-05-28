"""
This file is responsible for taking flattened python AST
and adding all of the methods to inject the values into pyobj type
for use with the runtime. the pyobj type has a 2 bit tag which
indicates the type of the object. the tag is used to determine
how to do operations on values. This is called explicate.
We have 3 basic types:
- int
- bool
- big
The big type is used for all other types.
"""

from ast import *
import inspect

from tree_utils import *
from pyyc_runtime import *
import explicate as exp
import P1

# Explicate

class Explicate(BodyStacker):
    ''' Explicate the AST. 
        All values need to be boxed and unboxed.
        All operations must check the type of the values and do the correct
        operation if it allowed. 
        We will translate this into calls to the runtime functions.
    '''
    def __init__(self, prefix='exp'):
        super().__init__(prefix=prefix)
        # Keep track of the function names so we don't add them twice
        self.function_names = []

    def explicate(self, func, inline=False, **kwargs):
        ''' Use inspect to get the source code of the function and parse it with AST.
            The function arguments will be replace by keyword. '''
        # Convert using ast
        s = inspect.getsource(func)
        # print(s)
        t = ast.parse(s)
        # print(ast.dump(t, indent=2))

        temp = self.get_temp()
        name_load = Name(id=temp, ctx=Load())
        # kwargs = {
        #     'target': Name(id=temp, ctx=Store()),
        #     **kwargs,
        # }
        # print(kwargs)
        if not inline:
            # Cause the function to be appended to the body (if it is not already there)
            self.prepend_FunctionDef(t.body[0])
            # Not sure if the order will be preserved...
            args = [kwargs[arg] for arg in kwargs.keys()]
            self.appendToCurrentBody(
                Assign(targets=[Name(id=temp, ctx=Store())],
                    value=Call(func=Name(id=func.__name__, ctx=Load()), args=args, keywords=[])
                )
            )
            return name_load
        raise Exception('Not implemented')

        # TODO: Finish implementing inline functions?
        # # Replace the arguments with the keyword arguments
        # class ArgReplacer(BodyStacker):
        #     def __init__(self, prefix, **kwargs):
        #         super().__init__(prefix)
        #         self.kwargs = kwargs
        #         self.function_args = []
        #     def visit_FunctionDef(self, node):
        #         self.function_args = [arg.arg for arg in node.args.args]
        #         return super().visit_FunctionDef(node)
        #     def visit_Name(self, node):
        #         if node.id in self.kwargs:
        #             return self.kwargs[node.id]
        #         if node.id in self.function_args:
        #             raise Exception(f'Function argument not specified: {node.id}')
        #         return node
        # t = ArgReplacer('exp_arg_repl_', **kwargs).transform(t)
        # # print(ast.dump(t, indent=2))
        
        # # visit everything in the body without pushing it to the stack
        # for stmnt in t.body[0].body:
        #     # self.visit(stmt)
        #     self.appendToCurrentBody(stmnt)
        # # super().visit(t.body[0])
        # # return [t.body[0]]
        # return name_load
    
    def prepend_FunctionDef(self, node):
        ''' Add the function to the TOP LEVEL body if it is not already there. '''
        if node.name not in self.function_names:
            self.function_names.append(node.name)
            self._body_stack[0].insert(0, node)

    def visit_Constant(self, node):
        return inject_constant(node)
    
    def visit_Subscript(self, node):
        self.generic_visit(node)
        # Make sure both the container and the key are name nodes
        val = node.value
        key = node.slice
        if not isinstance(val, ast.Name):
            val = self.replaceWithTemp(val)
        if not isinstance(key, ast.Name):
            key = self.replaceWithTemp(key)
        if isinstance(node.ctx, ast.Load):
            return get_subscript(val, key)
        elif isinstance(node.ctx, ast.Store):
            # Handle this case in Assign
            # return set_subscript(val, key, node.value)
            return node
        else:
            raise Exception('Invalid subscript context')
    
    def visit_Assign(self, node):
        self.generic_visit(node)
        if isinstance(node.targets[0], ast.Subscript) and isinstance(node.targets[0].ctx, ast.Store):
            obj = node.targets[0].value
            key = node.targets[0].slice
            val = node.value
            if not isinstance(key, ast.Name):
                key = self.replaceWithTemp(key)
            self.appendToCurrentBody(Expr(set_subscript(obj, key, val)))
            return None
        return node

    def visit_List(self, node):
        # Create and populate the list
        n = self.replaceWithTemp(inject_constant(ast.Constant(value=len(node.elts))), 'len')
        l = self.replaceWithTemp(inject_big(create_list(n)), 'list')
        for i, e in enumerate(node.elts):
            key = self.replaceWithTemp(inject_constant(ast.Constant(value=i)), 'idx')
            # We will implement constant injection later
            # i.e. key = Constant(value=((i << 2) | INT_TAG))
            # value = self.replaceWithTemp(inject_int(e), 'val')
            self.appendToCurrentBody(Expr(set_subscript(l, key, e)))
        return l

    def visit_Dict(self, node):
        # Create and populate the dict
        d = self.replaceWithTemp(inject_big(create_dict()), 'dict')
        for k, v in zip(node.keys, node.values):
            key = self.replaceWithTemp(self.visit(k), 'key')
            # value = self.replaceWithTemp(self.visit(v), 'val')
            self.appendToCurrentBody(Expr(set_subscript(d, key, v)))
        return d

    def visit_Call(self, node):
        self.generic_visit(node)
        # Replace builtin functions with runtime functions
        if P1.isInputInsideEval(node):
            return None

        s = ', '.join([unparse(n) for n in node.args])
        func_map = {
            'print': f'print_any({s})',
            'eval': f'eval_input_pyobj({s})',
        }
        # print(func_map)
        if node.func.id in func_map:
            return ast.parse(func_map[node.func.id]).body[0].value
        elif node.func.id == 'int':
            return self.explicate(exp.__int__, value=node.args[0])
        return node

    def visit_If(self, node):
        # wrap the test in is_true
        node.test = is_true(node.test)
        return super().visit_If(node)
        # return node

    def visit_While(self, node):
        # Do not visit the condition since it is embedded in the test of the if
        self._pushCurrentBody([])
        for stmt in node.body:
            self.visit(stmt)
        node.body = self._popCurrentBody()
        return node
    
    def visit_IfExp(self, node):
        raise Exception('IfExp should be converted to If by now')

    def visit_UnaryOp(self, node: UnaryOp):
        self.generic_visit(node)
        # UnaryOp:
        #   op: unaryop
        #       - USub
        #       - Not
        #   operand: expr
        if isinstance(node.op, ast.Not):
            # return BinOp(inject_int(Constant(value=1)), ast.BitXor(), inject_int(is_true(node.operand)))
            return self.explicate(exp.__not__, value=node.operand)
        elif isinstance(node.op, ast.USub):
            return self.explicate(exp.__neg__, value=node.operand)
        raise Exception('Not implemented')


    def visit_BoolOp(self, node):
        # BoolOp:
        #   op: boolop
        #   values: List[expr]
        # boolop:
        #   And
        #   Or
        assert(isinstance(node.op, ast.And) or isinstance(node.op, ast.Or))
        self.generic_visit(node)
        # if isinstance(node.op, ast.And):
        #     return explicate_add(node.values[0], node.values[1])
        return node

    def visit_BinOp(self, node):
        # BinOp:
        #   left: expr
        #   op: operator
        #   right: expr
        # operator:
        #   Add
        #   Sub
        #   Mult
        #   MatMult
        #   Div
        #   Mod
        #   Pow
        #   LShift
        #   RShift
        #   BitOr
        #   BitXor
        #   BitAnd
        #   FloorDiv
        assert(isinstance(node.op, ast.Add))
        return self.explicate(exp.__add__, left=node.left, right=node.right)

    def visit_Compare(self, node: Compare):
        # Compare:
        #   left: expr
        #   ops: List[cmpop]
        #   comparators: List[expr]
        # cmpop:
        #   Eq
        #   NotEq
        #   Lt
        #   LtE
        #   Gt
        #   GtE
        #   Is
        #   IsNot
        #   In
        #   NotIn
        self.generic_visit(node)
        if len(node.ops) != 1:
            raise Exception('Only one comparison is supported')
        op = node.ops[0]
        supported_ops = [ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is]
        if not isinstance(op, tuple(supported_ops)):
            print(op, type(op), file=sys.stderr)
            raise Exception('Unsupported comparison operator')
        return self.explicate(exp.cmp(op), left=node.left, right=node.comparators[0])
        return inject_bool(node)


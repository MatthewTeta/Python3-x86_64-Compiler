from ast import *

import pyyc_runtime
from IR import *

def getVariables(tree):
    # Generate a list of the unique variable names
    names = []
    for n in walk(tree):
        if isinstance(n, Name):
            if not n.id in names and not isBuiltin(n.id):
                names.append(n.id)
    # Generate a dictionary which maps the names to stack offsets -> {name: esp_offset}
    reg_map = {n: -(i + 1) * 4 for i, n in enumerate(names)}
    return reg_map
  
def insertParentPointers(n, parent = None):
    # Add the parent property
    n.parent = parent
    
    for c in iter_child_nodes(n):
      c.parent = n
      insertParentPointers(c, n)

def renameUserVariables(tree):
    for n in walk(tree):
        if isinstance(n, Name):
            if not isBuiltin(n.id):
                n.id = f'_{n.id}'
                # Add the name to the temp generator
                TempContext.temp_gen.add_user(n.id)
        elif isinstance(n, FunctionDef):
            n.name = f'_{n.name}'
        elif isinstance(n, arg):
            n.arg = f'_{n.arg}'

# def deleteFlatOnly(n):
#     l = []
#     def deleteFlatOnlyHelper(n):
#         if hasattr(n, 'flat_only'):
#             # n.parent.body.remove(n)
#             l.append(n)
#             pass
#         for c in iter_child_nodes(n):
#             deleteFlatOnlyHelper(c)
#     deleteFlatOnlyHelper(n)
#     for x in l:
#         print(x)
#         x.parent.body.remove(x)
#     # for c in iter_child_nodes(n):
#     #     # print(dump(n, indent=2))
#     #     print('\t', c)
#     #     deleteFlatOnly(c)
#     #     if hasattr(c, 'flat_only'):
#     #         # n.body.remove(c)
#     #         pass

def isSimple(n):
    for c in [Constant, Name, ir_Constant, ir_Name]:
        if isinstance(n, c):
            return True
    return False

def isBuiltin(s: str):
    # Returns true for builtins and runtime functions
    # TODO: Make this readable
    l = [(k, pyyc_runtime.__dict__[k]) for k in pyyc_runtime.__dict__.keys()]
    [v[0] for v in l if isinstance(v[1], type(lambda: 0))]
    for st in ['print', 'eval', 'input', 'int']:
        if s == st:
            return True
    return False

def isMod(n):
    return isinstance(n, (mod, ir_mod))

def isStmt(n):
    return isinstance(n, (stmt, ir_stmt))

def isExpr(n):
    return isinstance(n, (expr, ir_expr))

class SimpleCompare(Compare):
    _fields = ('left', 'ops', 'comparators')


class TempGenerator(set):
    ''' Singleton class which guarentees that all names added to it are unique.
        Used across all transformations for a given input file to guarentee that
        all temporaries are unique. AAlso keeps track of variables and their function scope.
    '''
    def __init__(self):
        super().__init__()
        self._temp_num = {}
        # Index the user variables by function name
        # self.builtin_vars = set()
        # self.runtime_vars = set()
        # self.user_vars = {
        #     'main': set('main')
        # }

    def add_user(self, name: str, func_name: str = 'main'):
        super().add(name)
        # if func_name not in self.user_vars:
        #     self.user_vars[func_name] = set()
        #     # Add the function name to the main scope
        #     self.user_vars['main'].add(func_name)
        # self.user_vars[func_name].add(name)

    def add(self, name: str):
        if name in self:
            raise Exception(f'Cannot add {name} to TempGenerator as it is already used.')
        # if name in self.user_vars['main']:
        #     raise Exception(f'Cannot add {name} to TempGenerator as it is used in the global scope.')
        super().add(name)

    def get(self, prefix: str = 't', func_name: str = 'main'):
        ''' Temp num incremented by prefix identifier '''
        if not prefix in self._temp_num:
            self._temp_num[prefix] = 0
        name = f'{prefix}{self._temp_num[prefix]}'
        assert(name not in self)
        self._temp_num[prefix] += 1
        # self.add_user(name, func_name)
        return name

    def reset(self):
        self._temp_num = {}
        self.clear()
        # self.user_vars.clear()

class TempContext:
    ''' Defines a TempGenerator for use with inheritance
    '''
    temp_gen = TempGenerator()

    def get_temp(self, prefix: str = None):
        return self.temp_gen.get(prefix)

class BodyStacker(NodeTransformer, TempContext):
    """ A NodeTransformer which keeps track of the current body of the tree

        It also provides a few helper functions for manipulating the tree:
        - replaceWithTemp: Replaces a node with a temporary variable
        - appendToCurrentBody: Appends a node to the current body
    """
    def __init__(self, prefix: str = 'f'):
        super().__init__()
        self.prefix = prefix
        self._body_stack = []
    
    def _pushCurrentBody(self, body):
        self._body_stack.append(body)

    def _popCurrentBody(self):
        return self._body_stack.pop()
    
    def _getCurrentBody(self):
        return self._body_stack[-1]
    
    def appendToCurrentBody(self, node: AST):
        self._body_stack[-1].append(node)

    def get_temp(self, alternate_prefix: str = None):
        prefix = alternate_prefix if alternate_prefix is not None else self.prefix
        return self.temp_gen.get(prefix)

    def replaceWithTemp(self, node: AST, alternate_prefix: str = None, body: list = None, index: int = -1):
        new_id = self.get_temp(alternate_prefix)
        new = Assign(targets=[Name(id=new_id, ctx=Store())], value=node)
        if body is None:
            if index == -1:
                self.appendToCurrentBody(new)
            else:
                self._getCurrentBody().insert(index, new)
        else:
            body.insert(index, new)
        return Name(id=new_id, ctx=Load())

    def visit_Module(self, node):
        self._pushCurrentBody([])
        self.generic_visit(node)
        node.body = self._popCurrentBody()
        return node
    
    def visit(self, node):
        # Wee need to preserve the original statements in the body
        # visitor = super.visit(node)
        visitor = NodeTransformer.visit(self, node)
        if isStmt(node):
            if visitor is not None:
                self._getCurrentBody().append(visitor)
        return visitor

    def visit_FunctionDef(self, node: FunctionDef):
        self._pushCurrentBody([])
        self.generic_visit(node)
        node.body = self._popCurrentBody()
        return node

    def visit_If(self, node):
        self.visit(node.test)
        self._pushCurrentBody([])
        for b in node.body:
            self.visit(b)
        node.body = self._popCurrentBody()
        self._pushCurrentBody([])
        for o in node.orelse:
            self.visit(o)
        node.orelse = self._popCurrentBody()
        # self.appendToCurrentBody(node)
        return node

    def visit_While(self, node):
        # This is arguably desugaring, but we need to put the test somewhere.
        # Convert to `while 1:` and add a break statement
        # but only if the test isn't already `while 1:`
        if not (isinstance(node.test, Constant) and node.test.value == 1):
            test = node.test
            node.test = Constant(value=1)
            iff = If(test=test, body=node.body, orelse=[Break()])
            test.parent = iff
            # iff.parent = node
            node.body = [iff]
        # Visit the transformed node
        self.visit(node.test)
        self._pushCurrentBody([])
        self.generic_visit(node)
        node.body = self._popCurrentBody()
        # self.appendToCurrentBody(node)
        return node

    # BEGIN IR NODES

    # def visit_ir_Module(self, node): ...

    def visit_ir_Function(self, node):
        # _fields = ('name', 'args', 'body', 'return_type', variables)
        self._pushCurrentBody([])
        self.generic_visit(node)
        node.body = self._popCurrentBody()
        return node

    def transform(self, tree: AST):
        ''' Must be called on a mod (e.g Module)
        '''
        # tt = c()
        # if isinstance(tree, Module):
        insertParentPointers(tree)
        tree = self.visit(tree)
        fix_missing_locations(tree)
        return tree

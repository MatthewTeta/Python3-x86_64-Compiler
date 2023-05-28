'''
This module contains the ClosureTransformer class which is used to
convert functions with free variables into closures. A closure is a
function that contains references to variables from an outer scope.
The first function argument will become a list of the free variables.
Any calls to this function will need to pass in the free variables.
The free variables from the closure will be destructured into the
function arguments. before the function body is executed.
'''

from ast import *

from tree_utils import *

class ClosureTransformer(BodyStacker):
    ''' Convert FunctionDef nodes to closures. Call nodes must
        pass in the free variables. '''

    def __init__(self, prefix='closure'):
        super().__init__()
        self.prefix = prefix
        self.functions = {}

    def visit_FunctionDef(self, node):
        # Find the free variables
        free_vars = self.find_free_vars(node)
        if free_vars:
            # # Rename all of the vars in the function
            # class VarRenamer(NodeTransformer):
            #     def visit_Name(self, node):
            #         node.id = f'cloj_{node.id}'
            #         return node
            # VarRenamer().visit(node)
            # free_vars = {f'cloj_{var}' for var in free_vars}
            # Create a new function
            new_func = self.create_closure(node, free_vars)
            # Add the new function to the list of functions
            self.functions[new_func.name] = free_vars
            # # Replace the old function with a call to the new function
            # return self.replace_with_closure_call(node, free_vars)
            return new_func
        return node

    def find_free_vars(self, node):
        ''' Find the free variables in a function. '''
        # Find the variables that are used in the function
        used_vars = self.find_used_vars(node)
        # Find the variables that are defined in the function
        defined_vars = self.find_defined_vars(node)
        # Find the variables that are free
        free_vars = used_vars - defined_vars
        return free_vars
    
    def find_used_vars(self, node):
        ''' Find the variables that are used in a function. '''
        used_vars = set()
        class UsedVarFinder(NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, Load):
                    used_vars.add(node.id)
        UsedVarFinder().visit(node)
        return used_vars
    
    def find_defined_vars(self, node):
        ''' Find the variables that are defined in a function. '''
        defined_vars = set()
        class DefinedVarFinder(NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, Store):
                    defined_vars.add(node.id)
            def visit_arg(self, node):
                defined_vars.add(node.arg)
        DefinedVarFinder().visit(node)
        return defined_vars
    
    def create_closure(self, node, free_vars):
        ''' Create a new function that is a closure. '''
        # Add the free variables as arguments
        node.args.args = [arg(arg=var) for var in free_vars] + node.args.args
        # Add the free variables to the body
        node.body = [Assign(targets=[Name(id=f'{var}', ctx=Store())], value=Name(id=var, ctx=Load())) for var in free_vars] + node.body
        return node

    def visit_Call(self, node):
        # Check if the function is a closure
        if node.func.id in self.functions:
            # Replace the function call with a call to the closure
            return self.replace_with_closure_call(node, self.functions[node.func.id])
        return node

    def replace_with_closure_call(self, node: Call, free_vars: list[str]):
        ''' Replace the function call with a call to the closure. '''
        # Create a list of the free variables
        free_vars_list = [Name(id=var, ctx=Load()) for var in free_vars]
        node.args = free_vars_list + node.args
        return node

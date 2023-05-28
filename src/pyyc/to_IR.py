import ast

from tree_utils import *
from IR import *

# NodeTransformer to convert python AST into IR_Module
class AST_to_IR(BodyStacker):
    '''
    Assuming flattened AST, convert it into an IR_Module
    '''
    def __init__(self, prefix: str = 'to_ir_'):
        super().__init__(prefix)
        self.functions = {
            'main': ir_Function(
                        name='main',
                        args=[],
                        body=[],
                        return_type=ir_void,
                        variables=set()),
        }
        # TODO: Variables are local to functions
        # Convert the set of variables to a set of IR_Variables
        # self.variables = {IR_Variable(v) for v in self.temp_gen.user_vars}

    def get_function(self, name: str):
        if name not in self.functions:
            raise Exception(f'Function {name} does not exist')
        return self.functions[name]
    
    def get_label(self, name: str):
        return ir_Label(name=self.get_temp(name))
    
    def insert_label(self, label: ir_Label):
        self.appendToCurrentBody(label)
    
    def insert_new_label(self, name: str):
        self.appendToCurrentBody(self.get_label(name))

    # def get_current_function(self):
    #     return self.get_function(self._getCurrentBody().name)

    def visit_Module(self, node):
        # Add return 0 to the end of main
        node.body.append(ast.Return(value=ast.Constant(value=0)))
        super().visit_Module(node)
        # self.generic_visit(node)
        self.functions['main'].body = node.body
        funcs = [self.get_function(name) for name in self.functions]
        return ir_Module(functions=funcs)
    
    def visit_FunctionDef(self, node: FunctionDef):
        super().visit_FunctionDef(node)
        rt = node.returns.id if node.returns else ir_void
        func = ir_Function(
            name=node.name,
            args=node.args.args,        # Only support simple args
            body=node.body,
            return_type=rt,
            variables=self.temp_gen)
        self.functions[node.name] = func
        return None

    def visit_Assign(self, node):
        # print("ASSIGN: ", getattr(node.targets[0], 'id', None), getattr(node, 'value', None))
        self.generic_visit(node)
        # print("ASSIGN: ", getattr(node.targets[0], 'id', None), getattr(node, 'value', None))
        val = node.value
        if isinstance(val, ir_trgt):
            val = ir_Target(target=val)
        return ir_Assign(
            target=node.targets[0],
            value=val)

    def visit_Expr(self, node):
        self.generic_visit(node)
        return ir_Expr(value=node.value)

    def visit_Return(self, node):
        self.generic_visit(node)
        return ir_Return(value=node.value)

    def visit_Call(self, node):
        self.generic_visit(node)
        # print("CALL: ", node.func)
        return ir_Call(func=node.func.id,
                    args=node.args)

    def visit_If(self, node):
        assert(isinstance(node.test, ast.Name) or isinstance(node.test, ast.Constant))
        label_then = self.get_label('if_then')
        label_else = self.get_label('if_else')
        label_end = self.get_label('if_end')
        # self.insert_label('if')
        # print("\n\nIF: ", node.test, label_then, label_else, label_end)
        node.test = self.visit(node.test)
        # print("IF: ", node.test, label_then, label_else, label_end, end='\n\n')
        self.appendToCurrentBody(
                ir_Branch(
                        condition=node.test,
                        true_label=label_then.name,
                        false_label=label_else.name))
        self.insert_label(label_then)
        for n in node.body:
            self.visit(n)
        self.appendToCurrentBody(
                ir_Jump(
                    label=label_end.name))
        self.insert_label(label_else)
        for n in node.orelse:
            self.visit(n)
        # self.appendToCurrentBody(Jump(label_end.name))
        self.insert_label(label_end)
        return None

    def visit_While(self, node):
        '''
        while 1:
            ...
            a = 1
            if a:
                ...
            else:
                break
        ...
        ==>
        while_cond:
            ...
            a = 1
            a = is_true(a)
            branch a, while_body, while_end
        while_body:
            ...
            jump while_cond
        while_end:
            ...
        '''
        assert(isinstance(node.test, ast.Constant) and bool(node.test.value))
        assert(len(node.orelse) == 0)
        assert(len(node.body) > 0 and isinstance(node.body[-1], ast.If))
        assert(len(node.body[-1].orelse) == 1 and isinstance(node.body[-1].orelse[0], ast.Break))
        # Don't visist the test, the test is always true (Desugar has replaced it with a constant)
        # The test is inside the if statement inside the body
        # node.test = self.visit(node.test)
        label_cond = self.get_label('while_cond')
        label_body = self.get_label('while_body')
        label_end = self.get_label('while_end')
        self.insert_label(label_cond)
        # Visit all but the last statement in the body (the If statement)
        for n in node.body[:-1]:
            self.visit(n)
        # Visist the If statement test
        test = self.visit(node.body[-1].test)
        self.appendToCurrentBody(
                ir_Branch(
                    condition=test, 
                    true_label=label_body.name, 
                    false_label=label_end.name))
        self.insert_label(label_body)
        for n in node.body[-1].body:
            self.visit(n)
        self.appendToCurrentBody(
                ir_Jump(
                    label=label_cond.name))
        self.insert_label(label_end)
        return None

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        assert(isinstance(node.op, ast.Not) or isinstance(node.op, ast.USub))
        return ir_UnaryOp(
            operand=node.operand,
            op=ir_Not() if isinstance(node.op, ast.Not) else ir_USub())

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Add):
            return ir_BinOp(left=node.left, right=node.right, op=ir_Add())
        elif isinstance(node.op, ast.BitXor):
            return ir_BinOp(left=node.left, right=node.right, op=ir_BitXor())
        raise Exception("Invalid binary operator for IR conversion! (Must be explicated)")

    def visit_BoolOp(self, node):
        raise Exception("BoolOp should not appear in the AST at this stage!")

    def visit_Compare(self, node):
        self.generic_visit(node)
        assert(len(node.ops) == 1 and len(node.comparators) == 1)
        cmpop_map = {
            ast.Eq: ir_Eq,
            ast.NotEq: ir_NotEq,
            ast.Lt: ir_Lt,
            ast.LtE: ir_LtE,
            ast.Gt: ir_Gt,
            ast.GtE: ir_GtE,
        }
        # This is the coolest little python trick!
        try:
            assert(isinstance(node.ops[0], tuple(cmpop_map.keys())))
        except:
            raise Exception("Invalid comparison operator for IR conversion! (Must be explicated)")
        return ir_Compare(left=node.left, right=node.comparators[0], op=cmpop_map[type(node.ops[0])]())

    def visit_arg(self, node):
        # self.generic_visit(node)
        # TODO: Add type by converting to IR_Type
        return ir_Name(id=node.arg, type=None)

    def visit_Name(self, node):
        # self.generic_visit(node)
        # TODO: Add type by converting to IR_Type
        # print(node.__class__)
        # print(node.id)
        n = ir_Name(id=node.id, type=None)
        # print(n.__class__)
        return n

    def visit_Constant(self, node):
        # self.generic_visit(node)
        t = ir_bool if isinstance(node.value, bool) else ir_int
        # Convert bool to int for IR
        v = int(node.value)
        return ir_Constant(value=v, type=t)

    def visit_Break(self, node):
        # These are handled in the If statements
        return None

    def transform(self, tree: ast.Module):
        tree: ir_mod = super().transform(tree)
        # # populate the 'variables' set for each function
        # for func in tree.functions:
        #     for n in ast.walk(func):
        #         if isinstance(n, ir_Name):
        #             print(n.id)
        #             func.variables.add_user(n.id)
        #     print(func.name, func.variables)

        # verify_ir(tree)
        return tree

    ...

# class x86_IR_Transformer(ast.NodeVisitor, TempContext):
#     def __init__(self, prefix: str = 'r'):
#         self.prefix = prefix
#         self.statements = []
#         # Convert the set of variables to a set of IR_Variables
#         self.variables = {IR_Variable(v) for v in self.temp_gen}

#     def get_temp(self, alternate_prefix: str = None):
#         prefix = alternate_prefix if alternate_prefix else self.prefix
#         return self.temp_gen.get(prefix)

#     def get_variable(self, name: str):
#         """ Get a variable from the set of variables, or create it if it doesn't exist.
#             This way, The IR_Variables will be the same for the same variable name.
#             We can use them for the graph coloring algorithm.
#         """
#         # Check if the variable exists
#         for v in self.variables:
#             if v.name == name:
#                 return v
#         raise Exception(f'Variable {name} does not exist')

#     def add_statement(self, *args, **kwargs):
#         self.statements.append(IR_Statement(*args, **kwargs))

#     def create_label(self, label_type: str = 'label'):
#         temp = self.get_temp(label_type)
#         label = IR_Statement(IR_Statement.LABEL, str_arg=temp)
#         return label

#     def visit_Assign(self, n):
#         # TODO: Fix comments
#         # comment = ast.unparse(n)
#         comment = None
#         self.generic_visit(n)
#         # Locate the index of the var
#         dest = n.targets[0].IR
#         # The value can be either:
#         #   A Constant
#         #   A Name
#         #   A BinOp add
#         #   A UnaryOp neg
#         #   A Call to eval(input())
#         if isinstance(n.value, ast.Constant) or isinstance(n.value, ast.Name):
#             self._add_statement(IR_Statement(IR_Statement.MOVE, n.value.IR, dest, comment=comment))
#         if isinstance(n.value, ast.UnaryOp):
#             # Move the constant into the assignment target and then make it negative
#             self._add_statement(IR_Statement(IR_Statement.MOVE, n.value.operand.IR, dest, comment=comment))
#             self._add_statement(IR_Statement(IR_Statement.NEG, dest, n.value.operand.IR, comment=comment))
            
#             # self._add_statement(IR_Statement(IR_Statement.NEG, n.value.operand.IR, dest, comment=comment))
#         elif isinstance(n.value, ast.BinOp):
#             # Determine if the if either of the operands are constants
#             # x = a + b
#             # x = a + x
#             # x = x + a
#             # x = 1 + x
#             # x = x + 1
#             # x = 1 + 1
#             # x = 1 + a
#             # x = a + 1
#             # So in the case of a BinOp, we need to check if the left or right operands are shared with the source, if they are not,
#             # then we must use a temporary variable to store the result of the BinOp add
#             if isinstance(n.value.left.IR, IR_Variable) and n.value.left.IR.name == dest.name:
#                 # The left is the same as the destination, so we do not need to use a temporary variable
#                 # x = x + a
#                 self._add_statement(IR_Statement(IR_Statement.ADD, n.value.right.IR, dest, comment=comment))
#             elif isinstance(n.value.right.IR, IR_Variable) and n.value.right.IR.name == dest.name:
#                 # The right is the same as the destination, so we do not need to use a temporary variable
#                 # x = a + x
#                 self._add_statement(IR_Statement(IR_Statement.ADD, n.value.left.IR, dest, comment=comment))
#             else:
#                 # We need to use a temporary variable to store the result of the BinOp add
#                 # x = a + b
#                 # must expand to:
#                 # temp = a
#                 # temp = temp + b
#                 # x = temp
#                 # TODO: Switch to this
#                 # x = a
#                 # x = x + b
#                 # temp = self._create_temporary()
#                 self._add_statement(IR_Statement(IR_Statement.MOVE, n.value.left.IR, dest, comment=comment))
#                 self._add_statement(IR_Statement(IR_Statement.ADD, n.value.right.IR, dest, comment=comment))
#                 # self._add_statement(IR_Statement(IR_Statement.MOVE, temp, dest, comment=comment))
#         elif isinstance(n.value, ast.Call):
#             # Check if this is an eval_input
#             if n.value.func.id == 'eval':
#                 self._add_statement(IR_Statement(IR_Statement.CALL, dest=dest, str_arg='eval_input_int', comment=comment))
#             if n.value.func.id == 'int':
#                 # Check the type of logical comparison
#                 if isinstance(n.value.args[0], ast.UnaryOp):
#                     # This is a not
#                     #raise NotImplementedError('Not implemented: TODO: Add support for not (desugar in the flattener)')
#                     operand = n.value.args[0].operand
#                     # This is a negation 
#                     # x = int(not a):
#                     # cmpl $0, a
#                     # sete %al
#                     # movzbl %al, x
#                     self._add_statement(IR_Statement(IR_Statement.CMP, IR_Constant(0), operand.IR))
#                     self._add_statement(IR_Statement(IR_Statement.SETEQ, IR_REG_AL))
#                     self._add_statement(IR_Statement(IR_Statement.MOVZBL, IR_REG_AL, dest))

#                 elif isinstance(n.value.args[0], ast.Compare):
#                     # This is a logical comparison
#                     # Case 1:
#                     # x = int(a == b):
#                     # cmpl a, b
#                     # sete %al
#                     # movzbl %al, x
#                     # Case 2:
#                     # x = int(a != b):
#                     # cmpl a, b
#                     # setne %al
#                     # movzbl %al, x
#                     # Case 3:
#                     # x = int(a == b != c):
#                     # # Not implemented
#                     left = n.value.args[0].left.IR
#                     right = n.value.args[0].comparators[0].IR
#                     op = n.value.args[0].ops[0]
#                     self._add_statement(IR_Statement(IR_Statement.CMP, left, right))
#                     if isinstance(op, ast.Eq):
#                         self._add_statement(IR_Statement(IR_Statement.SETEQ, IR_REG_AL))
#                     elif isinstance(op, ast.NotEq):
#                         self._add_statement(IR_Statement(IR_Statement.SETNE, IR_REG_AL))
#                     else:
#                         raise NotImplementedError('Not implemented')
#                     self._add_statement(IR_Statement(IR_Statement.MOVZBL, IR_REG_AL, dest))
#         return n
    
#     def visit_Expr(self, n):
#         # comment = ast.unparse(n)
#         comment = None
#         self.generic_visit(n)
#         # Function calls may have side effects
#         if isinstance(n.value, ast.Call):
#             if n.value.func.id == 'eval':
#                 self._add_statement(IR_Statement(IR_Statement.CALL, str_arg='eval_input_int', comment=comment))
#         return n
    
#     def visit_UnaryOp(self, n):
#         self.generic_visit(n)
#         return n
        
#     def visit_BinOp(self, n):
#         self.generic_visit(n)
#         return n
    
#     def visit_If(self, n):      # TODO - Add support for if/else
#         # comment = ast.unparse(n)
#         comment = None
#         self.visit(n.test)
#         # Create a new label for the then
#         then_label = self._create_label_then()
        
#         # create a new statement for the comparison
#         # Create a new statement for the if using cmp
#         self._add_statement(IR_Statement(IR_Statement.CMP, n.test.IR , IR_Constant(0)))
#         else_label = self._create_label_else()
#         self._add_statement(IR_Statement(IR_Statement.JUMPEQ, str_arg=else_label.str_arg))
#         # Add the statements from the if body
#         self._add_statement(then_label)
#         for statement in n.body:
#             self.visit(statement)
#         # Add the jump to the end of the if
#         endif_label = self._create_label_endif()
#         self._add_statement(IR_Statement(IR_Statement.JUMP, str_arg=endif_label.str_arg))
#         # Add the else label
#         self._add_statement(else_label)
#         # Add the statements from the else body
#         for statement in n.orelse:
#             self.visit(statement)
#         # Add the endif label
#         self._add_statement(endif_label)
        
#         return n
        
#     def visit_While(self, n):  # TODO - Add support for while loops
#         # Visit the test
#         self.visit(n.test)
#         # Get the labels
#         l_cond, l_body, l_end = self._create_label_while()
#         # Move n.conditionals into flattened basic block indicated by a label
#         self._add_statement(l_cond)
#         for statement in n.conditionals:
#             self.visit(statement)
#         # Compare the test to 0
#         self._add_statement(IR_Statement(IR_Statement.CMP, n.test.IR, IR_Constant(0)))
#         # Add conditional jump to end of conditional block
#         self._add_statement(IR_Statement(IR_Statement.JUMPEQ, str_arg=l_end.str_arg))
#         # Fall through to the body
#         # Add the body
#         self._add_statement(l_body)
#         for statement in n.body:
#             self.visit(statement)
#         # Add the jump to the conditionals
#         self._add_statement(IR_Statement(IR_Statement.JUMP, str_arg=l_cond.str_arg))
#         # Add the end label
#         self._add_statement(l_end)
#         #self.generic_visit(n)
#         return n
    

#     def visit_Call(self, n):
#         self.generic_visit(n)
#         # Do nothing if this is an input call
#         if n.func.id == 'input':
#             pass
#         if n.func.id == 'eval':
#             # self._add_statement(IR_FunctionCall('eval_input_int', []))
#             pass
#         if n.func.id == 'print':
#             self._add_statement(IR_Statement(IR_Statement.CALL, src=n.args[0].IR, str_arg='print_int_nl', comment=None))
#         return n
    
#     def visit_Name(self, n):
#         if not isBuiltin(n.id):
#             n.IR = self._get_variable(n.id)
#         return n
    
#     def visit_Constant(self, n):
#         n.IR = IR_Constant(n.value)
#         return n

#     def transform(self, tree):
#         insertParentPointers(tree)
#         self.visit(tree)
#         fix_missing_locations(tree)
#         return IR_Function(self.statements, self.variables, x86_color_registers)


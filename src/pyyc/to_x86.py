'''
Convert IR Module to x86.
Incorporates ABI and calling conventions.
Also needs to know the platform (x86_64, x86, etc.)
For now this only works for x86_64
'''

from typing import Dict
from tree_utils import BodyStacker
from IR import *
from x86 import *
from lambda_util import *

VAR_SIZE = 8

class ir_Module_to_x86_Transformer(BodyStacker):
    '''
    Convert IR Module to x86.
    Sometimes we will need to create temporaries. In this case we need to restart the conversion...
    We will think about register spilling soon...
    For each function:
    1. Flatten the IR into two op code IR
    2. Assign registers to variables
    3. Add supporting statements and convert all IR to x86
    '''
    def __init__(self, prefix: str = 'x86'):
        super().__init__(prefix)
        self.og_prefix = prefix
        self.current_function = ''

    def visit(self, node):
        # print(f"VISITING: {node.__class__.__name__} -> {node}")
        return super().visit(node)

    def appendToCurrentBody(self, node):
        # print(f'Appending {node}')
        self.has_spilled = True
        return super().appendToCurrentBody(node)

    def get_temp(self, alternate_prefix: str = None):
        return super().get_temp(alternate_prefix)
    
    def replaceWithTemp(self, node, alternate_prefix: str = None):
        new_id = self.get_temp(alternate_prefix)
        new = ir_Assign(target=ir_Name(id=new_id), value=node)
        self.appendToCurrentBody(new)
        return ir_Name(id=new_id)
    
    """ def visit_ir_Module(self, node):
        self.generic_visit(node)
        self.functions = {f.name for f in node.functions}
        return node"""

    def visit_ir_Function(self, node):
        # Delete the function if it is empty
        if len(node.body) == 0:
            return None

        self.current_function = node.name

        # Do an initial visits to convert all IR to x86
        i = 0
        while True:
            # print(f'Flattening {node.name} {i}')
            self.has_spilled = False
            self.prefix = f'{self.og_prefix}_{node.name}_1_{i}'
            super().visit_ir_Function(node)
            # if we have not spilled, we are done
            # print()
            # print_ir(node)
            # print()
            # input('Press enter to continue...')
            # print()
            if not self.has_spilled:
                break
            i += 1

        # Make sure we have a return statement
        if not isinstance(node.body[-1], x86_Ret):
            node.body.append(x86_Ret())
        return_stmnt = node.body.pop()

        # Make sure all of the statements are x86
        for stmnt in node.body:
            try:
                assert(isinstance(stmnt, x86_stmnt))
            except:
                print(stmnt)
                raise

        print("x86 before register assignment: ")
        print_ir(node)

        # Do register assignment
        self.assign_registers(node)

        # Generate the prologue and epilogue
        self.frame_function(node, return_stmnt=return_stmnt)

        # Make sure all of the statements are x86
        for stmnt in node.body:
            for n in ast.walk(stmnt):
                try:
                    assert(n.__class__.__name__.startswith('x86_'))
                except:
                    print(f"ERROR: IR node ('{n.__class__.__name__}') found after register assignment: ", n)
                    raise

        return node

    def visit_ir_Assign(self, node):
        self.generic_visit(node)
        try:
            assert(isinstance(node.target, ir_Name))
        except AssertionError:
            print(node, node.target, node.value, file=sys.stderr)
            raise
        target = node.target.id
        # Make sure add is in two operand form
        if isinstance(node.value, ir_Target):
            # TODO: Do this after register assignment
            # # Remove the statment if the target is the same as the source
            # if isinstance(node.value.target, ir_Name) and node.value.target.id == target:
            #     return None
            return x86_Movq(
                src=node.value.target,
                dst=node.target)
        elif isinstance(node.value, ir_Call):
            self.appendToCurrentBody(self.call_function(node.value))
            return x86_Movq(
                src=x86_Registers['rax'],
                dst=node.target)
        elif isinstance(node.value, ir_BinOp):
            if isinstance(node.value.op, ir_BitXor):
                new = x86_Xorq(src=node.value.left, dst=node.value.right)
            elif isinstance(node.value.op, ir_Add):
                new = x86_Add(src=node.value.left, dst=node.value.right)
            else:
                raise NotImplementedError(f"BinOp {node.value.op} not implemented")
            # # If both operands are constants, we need to create a temporary
            # We want the right argument to be the same as the target
            if isinstance(node.value.right, ir_Name) and node.value.right.id == target:
                new.src = node.value.left
                new.dst = node.value.right
            if isinstance(node.value.left, ir_Name) and node.value.left.id == target:
                new.src = node.value.right
                new.dst = node.value.left
            else:
                # Neither operand is the target, so we first assign the target to the left operand
                self.appendToCurrentBody(ir_Assign(target=node.target, value=ir_Target(node.value.right)))
                node.value.right = node.target
                new.src = node.value.left
                new.dst = node.value.right
            return new
        elif isinstance(node.value, ir_UnaryOp):
            if isinstance(node.value.op, (ir_USub, ir_Not)):
                # See if we can do it in place
                if isinstance(node.value.operand, ir_Name) and node.value.operand.id == target:
                    # We can do it in place
                    return x86_Neg(node.value.operand)
                else:
                    # We need to do it in two steps
                    self.appendToCurrentBody(ir_Assign(target=node.target, value=ir_Target(node.value.operand)))
                    # if isinstance(node.value.op, ir_Not):
                    #     return x86_Not(x86_And(node.target, x86_Constant(4)))
                    return x86_Neg(node.target)
            # elif isinstance(node.value.op, ir_Not):
            #     raise Exception("ir_UnaryOp (ir_Not) should be explicated by now")
        elif isinstance(node.value, ir_Compare):
            cmpop_map = {
                ir_Eq: x86_SetE,
                ir_NotEq: x86_SetNE,
                ir_Lt: x86_SetL,
                ir_LtE: x86_SetLE,
                ir_Gt: x86_SetG,
                ir_GtE: x86_SetGE,
            }
            assert(isinstance(node.value.op, tuple(cmpop_map.keys())))
            op = cmpop_map[type(node.value.op)]
            # Idea: Populate the x86_Set* with an empty register and let it be filled in later
            # The register allocator can use the restrictions on this shell to guide it's decision
            # for the target register...
            # For now we will just use a static register (al)
            self.appendToCurrentBody(x86_Cmp(src=node.value.left, dst=node.value.right))
            self.appendToCurrentBody(op(dst=x86_Registers['al']))
            self.appendToCurrentBody(x86_Movzbq(src=x86_Registers['al'], dst=node.target))
            return None
        raise NotImplementedError('Assign not implemented for {}'.format(node.value.__class__.__name__))
    
    def visit_ir_Expr(self, node):
        self.generic_visit(node)
        invalid_expr = (ir_Target, ir_BinOp, ir_UnaryOp, ir_Compare)
        if isinstance(node.value, invalid_expr):
            # Get rid of the expression
            return None
        elif isinstance(node.value, ir_Call):
            return self.call_function(node.value)

    def visit_ir_Label(self, node):
        return x86_Label(name=node.name)

    def visit_ir_Constant(self, node):
        return x86_Constant(value=node.value)

    def visit_ir_Return(self, node):
        self.generic_visit(node)
        # TODO: Handle multiple return values
        # Move the return value to rax
        if isinstance(node.value, ir_trgt):
            self.appendToCurrentBody(x86_Movq(src=node.value, dst=x86_Registers['rax']))
            self.appendToCurrentBody(x86_Jmp(name=f'end_{self.current_function}'))
        return None

    def visit_ir_Jump(self, node):
        return x86_Jmp(name=node.label)

    def visit_ir_Branch(self, node):
        # TODO: Make this more strict to where it only accepts ir_Name
        assert(isinstance(node.condition, ir_trgt))
        self.generic_visit(node)
        # Compare the condition to zero
        self.appendToCurrentBody(x86_Cmp(src=x86_Constant(value=0), dst=node.condition))
        # Jump if the condition is true
        return x86_Je(name=node.false_label)
        # Jump if the condition is false (we don't need to do this, but it is more clear)
        # I would add it except is creates an edge case in the CFG generation
        # self.appendToCurrentBody(x86_Jmp(name=node.true_label))
    
    def call_function(self, node: ir_Call):
        # Pass the arguments in using the calling convention
        # x86: Pass the first 6 arguments in registers
        # - rdi, rsi, rdx, rcx, r8, r9
        # - The rest on the stack
        regs = ('rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9')
        regs = (x86_Registers[reg] for reg in regs)
        while len(node.args) > 6:
            # Pop the 7th argument off the stack
            arg = node.args.pop(6)
            # Push it onto the stack
            self.appendToCurrentBody(x86_Push(src=arg))
        # Move the remaining arguments into the registers
        for arg, reg in zip(node.args, regs):
            # print(arg, reg)
            self.appendToCurrentBody(x86_Movq(src=arg, dst=reg))
        # Call the function
        return x86_Call(func=node.func)
    
    def frame_function(self, node: ir_Function, return_stmnt: x86_Ret):
        '''
        Generate the calling convention for the function.
        Assuming there is a return at the end of the function
        '''
        # Get the registers used in the function and the stack size
        node_registers, memory_locations = x86_get_function_registers(node)
        prologue = []
        epilogue = []
        # Insert function directive .globl <name>
        # Insert a label at the beginning of the function
        prologue = [
            x86_Directive(directive='.globl', args=[node.name]),
            x86_Directive(directive='.type', args=[node.name, '@function']),
            x86_Label(name=node.name),
        ]
        # if len(memory_locations) > 0:
        prologue.extend([
            x86_Push(src=x86_Registers['rbp']),
            x86_Movq(src=x86_Registers['rsp'], dst=x86_Registers['rbp']),
        ])
        # Push all of the callee-saved registers which are used in the program
        saved_regs = 0
        for reg in node_registers:
                reg = x86_Registers[reg]
                if reg.caller_save:
                    r = reg
                    if is8BitRegister(reg.id):
                        # print('8 bit register')
                        # r = x86_Registers[r.equivalent[0]]
                        # print(r)
                        continue
                    prologue.append(x86_Push(src=r))
                    epilogue.append(x86_Pop(dst=r))
                    saved_regs += 1
        # Reverse the epilogue to get the correct order of popping
        epilogue += [x86_Label(name=f'end_{node.name}')]
        epilogue.reverse()
        # allocate stack space if necessary
        # TODO: This should be done in the register allocator
        # Determine the stack space needed for the function rounding up to a multiple of 16
        # TODO: Check if this is right
        stack_size = len(memory_locations)
        stack_size = (((stack_size * VAR_SIZE) + 15) & ~15) + (VAR_SIZE * (saved_regs) % 16)
        # print(f'Stack size: {stack_size} bytes')
        if stack_size > 0:
            prologue.append(x86_Sub(src=x86_Constant(value=stack_size), dst=x86_Registers['rsp']))
            # epilogue.insert(0, x86_Add(src=x86_Constant(value=stack_size), dst=x86_Registers['rsp']))
        # Add the function epilogue (ABI) statements
        # if len(memory_locations) > 0:
        epilogue.extend([
            x86_Movq(src=x86_Registers['rbp'], dst=x86_Registers['rsp']),
            x86_Pop(dst=x86_Registers['rbp']),
        ])
        epilogue.append(return_stmnt)
        # Add directives for size and alignment
        epilogue.extend([
            x86_Directive(directive='.size', args=[node.name, f'.-{node.name}'], indent=True),
            x86_Directive(directive='.align', args=[16], indent=True),
        ])

        # Rebuild the body with the prologue and epilogue placed correctly
        node.body = prologue + node.body + epilogue
        # for i, stmnt in enumerate(node.body):
        #     # Epilogue should be placed before the return statement
        #     if i == len(node.body) - 2:
        #         body.extend(epilogue)
        #     body.append(stmnt)
        # node.body = body

        return node
    
    def assign_registers(self, node: ir_Function):
        '''
        Assign registers to variables
        '''
        # print(node.args, node.variables, file=sys.stderr)
        # print([type(var) for var in node.args], file=sys.stderr)
        # Now we need to do register allocation

        # def _get_register_allocations(node: ir_Function, register_assignments: Dict[ir_trgt, Union[x86_Register, x86_Memory]]):
        #     node.update_variables()
        #     # # Create CFG
        #     # cfg = CFG(node)
        #     # # Do liveness analysis
        #     # liveness = Liveness(cfg)
        #     # # Create interference graph
        #     # interference = InterferenceGraph(liveness)
        #     # # Do register allocation
        #     # register_allocation = RegisterAllocation(interference)
        #     # # Assign registers
        #     # for var in node.variables:
        #     #     if var in register_allocation.register_allocations:
        #     #         self.register_assignments[var] = x86_Register(register_allocation.register_allocations[var])
        #     #     else:
        #     #         # We need to spill this variable
        #     #         self.has_spilled = True
        #     # Naive register allocation
        #     # Put everything on the stack
        #     register_assignments = { var: x86_Memory(base=x86_Registers['rbp'], offset=VAR_SIZE * i) for i, var in enumerate(node.variables)}
        #     return register_assignments

        i = 0
        while True:
            self.has_spilled = False
            self.prefix = f'{self.og_prefix}_{node.name}_2_{i}'
            # register_assignments = { arg.id: x86_Registers[argument_registers[i]] for i, arg in enumerate(node.args) }
            register_assignments = {}
            node.update_variables()
            # register_assignments = { var: x86_Memory(base=x86_Registers['rbp'], offset=-(VAR_SIZE * (i))) for i, var in enumerate(node.variables) if var not in register_assignments}
            for i, var in enumerate(node.variables):
                if var not in register_assignments.keys():
                    register_assignments[var] = x86_Memory(base=x86_Registers['rbp'], offset=-(VAR_SIZE * (i+1)))
            # print(register_assignments)
            break
            # # if we have not spilled, we are done
            # if not self.has_spilled:
            #     break
            # i += 1
        # Move the arguments to the correct registers
        argument_registers = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        for i, arg in enumerate(node.args):
            if i < len(argument_registers):
                # register_assignments[arg.id] = x86_Registers[argument_registers[i]]
                node.body.insert(0, x86_Movq(src=x86_Registers[argument_registers[i]], dst=register_assignments[arg.id]))
            else:
                raise NotImplementedError('Too many arguments')


        # Replace all ir_Name nodes with the new register assignments from the dict map
        #functions = self.functions
        class ir_Name_to_x86_Location(BodyStacker):
            def visit_ir_Name(_, node):
                if str(node.id).startswith('lambda'):
                    return x86_Label(name=node.id)
                return register_assignments[node.id]
        ir_Name_to_x86_Location().visit(node)

        
        # Visit the function again to fix x86 instructions with too many memory references
        node.register_assignments = register_assignments
        super().visit_ir_Function(node)

        get_calls(node,register_assignments)


    def visit_x86_Movq(self, node: x86_Movq):
        '''
        Fix x86_Movq instructions with too many memory references
        '''
        # If the source is a memory location and the destination is a memory location
        if (isinstance(node.src, x86_Memory)or isinstance(node.src, x86_Label)) and isinstance(node.dst, x86_Memory):
            # We need to move the source to a register first
            # self.appendToCurrentBody(x86_Movq(src=node.src, dst=x86_Registers['rax']))
            # return x86_Movq(src=x86_Registers['rax'], dst=node.dst)
            return x86_Movq(src=self.move_to_register(node.src), dst=node.dst)
        return node

    def visit_x86_Xorq(self, node: x86_Movq):
        '''
        Fix x86_Movq instructions with too many memory references
        '''
        # If the source is a memory location and the destination is a memory location
        if isinstance(node.src, x86_Memory) and isinstance(node.dst, x86_Memory):
            # We need to move the source to a register first
            # self.appendToCurrentBody(x86_Movq(src=node.src, dst=x86_Registers['rax']))
            # return x86_Movq(src=x86_Registers['rax'], dst=node.dst)
            return x86_Xorq(src=self.move_to_register(node.src), dst=node.dst)
        return node
    
    def visit_x86_Movzbq(self, node: x86_Movzbq):
        '''
        Fix x86_Movzbq instructions with too many memory references
        '''
        # If the source is a memory location and the destination is a memory location
        if isinstance(node.dst, x86_Memory):
            # This one is special since this instruction is used with 'al' as the source
            # This one is special because the temp register is the destination
            # return x86_Movzbq(src=node.src, dst=self.move_to_register(node.dst))
            temp = self.get_reg_sequential()
            self.appendToCurrentBody(x86_Movzbq(src=node.src, dst=temp))
            return x86_Movq(src=temp, dst=node.dst)
        return node
    
    def visit_x86_Add(self, node: x86_Add):
        '''
        Fix x86_Add instructions with too many memory references
        '''
        # If the source is a memory location and the destination is a memory location
        if isinstance(node.src, x86_Memory) and isinstance(node.dst, x86_Memory):
            # We need to move the source to a register first
            # self.appendToCurrentBody(x86_Movq(src=node.src, dst=x86_Registers['rax']))
            # return x86_Add(src=x86_Registers['rax'], dst=node.dst)
            return x86_Add(src=self.move_to_register(node.src), dst=node.dst)
        return node

    def visit_x86_Cmp(self, node: x86_Cmp):
        '''
        Fix x86_Cmp instructions with too many memory references
        '''
        # If the source is a memory location and the destination is a memory location
        if isinstance(node.src, x86_Memory) and isinstance(node.dst, x86_Memory):
            return x86_Cmp(src=self.move_to_register(node.src), dst=self.move_to_register(node.dst))
        if isinstance(node.src, x86_Constant) and isinstance(node.dst, x86_Constant):
            # We need to move the source to a register first
            # self.appendToCurrentBody(x86_Movq(src=node.src, dst=x86_Registers['rax']))
            # return x86_Cmp(src=x86_Registers['rax'], dst=node.dst)
            return x86_Cmp(src=node.src, dst=self.move_to_register(node.dst))
        return node

    def move_to_register(self, node: x86_Memory, register: x86_Register = None):
        '''
        Move the source to a register
        '''
        if register is None:
            register = self.get_reg_sequential()
        # We need to move the source to a register first
        self.appendToCurrentBody(x86_Movq(src=node, dst=register))
        return register

    def get_reg_sequential(self):
        '''
        Get a register sequentially
        '''
        reg = x86_Registers[list(x86_Registers.keys())[int(self.get_temp('')) % len(x86_Registers)]]
        if reg.is8Bit() or reg.isReserved():
            reg = self.get_reg_sequential()
        return reg


    ...

# def to_x86(ir_module: ir_Module) -> List[x86_stmnt]:
#     '''
#     Convert IR Module to x86
#     '''
#     assert(isinstance(ir_module, ir_Module))
#     x86_module = []
#     for fnct in ir_module.functions:
#         x86_module.extend(to_x86_fnct(fnct))
#     return x86_module


# def to_x86_fnct(ir_fnct: ir_Function) -> List[x86_stmnt]:
#     '''
#     Convert IR Function to x86
#     '''
#     assert(isinstance(ir_fnct, ir_Function))
#     # iterate until no more changes (changes can compound because of spill variables, etc.)
#     def function_to_x86(ir_fnct: ir_Function, old_x86_fnct: ir_Function) -> List[x86_stmnt]:
#         s_old = StringIO()
#         print_ir(old_x86_fnct, file=s_old)
#         # Begin the transformation
#         x86_fnct = []
#         x86_fnct.append(x86_Push(x86_Register('rbp')))
#         x86_fnct.append(x86_Movq(x86_Register('rsp'), x86_Register('rbp')))
#         x86_fnct.append(x86_Sub(x86_Constant(8*len(ir_fnct.variables)), x86_Register('rsp')))
#         ir_fnct_to_x86_Transformer().transform(ir_fnct)
#         x86_fnct.extend(func)
#         x86_fnct.append(x86_Add(x86_Constant(8*len(ir_fnct.variables)), x86_Register('rsp')))
#         x86_fnct.append(x86_Pop(x86_Register('rbp')))
#         x86_fnct.append(x86_Ret())
#         ir_fnct.body = x86_fnct
#         # use the print_ir function to deep compare the IR
#         s_new = StringIO()
#         print_ir(x86_fnct, file=s_new)
#         if s_old.getvalue() == s_new.getvalue():
#             return ir_fnct
#         # Recurse
        
#         return function_to_x86(ir_fnct, x86_fnct)

#     function_to_x86(ir_fnct, ir_void)



# # def to_x86_fnct(ir_fnct: ir_Function) -> List[x86_stmnt]:
# #     '''
# #     Convert IR Function to x86
# #     '''
# #     assert(isinstance(ir_fnct, ir_Function))
# #     x86_fnct = []
# #     x86_fnct.append(x86_Push(x86_Register('rbp')))
# #     x86_fnct.append(x86_Mov(x86_Register('rsp'), x86_Register('rbp')))
# #     x86_fnct.append(x86_Sub(x86_Constant(8*len(ir_fnct.variables)), x86_Register('rsp')))
# #     for stmnt in ir_fnct.body:
# #         x86_fnct.extend(to_x86_stmnt(stmnt))
# #     x86_fnct.append(x86_Add(x86_Constant(8*len(ir_fnct.variables)), x86_Register('rsp')))
# #     x86_fnct.append(x86_Pop(x86_Register('rbp')))
# #     x86_fnct.append(x86_Ret())
# #     return x86_fnct

# # def to_x86_stmnt(ir_statement: ir_stmnt) -> List[x86_stmnt]:
# #     '''
# #     Convert IR Statement to x86
# #     '''
# #     assert(isinstance(ir_statement, ir_stmnt))
# #     x86_stmnts = []
# #     if isinstance(ir_statement, ir_Assign):
# #         x86_stmnts.extend(to_x86_assign(ir_statement))
# #     elif isinstance(ir_statement, ir_Expr):
# #         x86_stmnts.extend(to_x86_expr(ir_statement))
# #     elif isinstance(ir_statement, ir_Return):
# #         x86_stmnts.extend(to_x86_return(ir_statement))
# #     else:
# #         raise Exception(f'Unknown IR Statement: {ir_statement}')
# #     return x86_stmnts

# # def to_x86_assign(ir_assign: ir_Assign) -> List[x86_stmnt]:
# #     '''
# #     Convert IR Assign to x86
# #     '''
# #     assert(isinstance(ir_assign, ir_Assign))
# #     x86_stmnts = []
# #     if isinstance(ir_assign.value, ir_Constant):
# #         x86_stmnts.append(x86_Mov(ir_assign.value, ir_assign.target))
# #     elif isinstance(ir_assign.value, ir_Target):
# #         x86_stmnts.append(x86_Mov(ir_assign.value, ir_assign.target))
# #     elif isinstance(ir_assign.value, ir_BinOp):
# #         # x86_stmnts.extend(to_x86_binop(ir_assign.value, ir_assign.target))
# #         raise Exception('Not implemented')
# #     elif isinstance(ir_assign.value, ir_UnaryOp):
# #         # x86_stmnts.append(x86_Neg(ir_assign.target))
# #         # TODO: Handle temp variables
# #         raise Exception('Not implemented')
# #     else:
# #         raise Exception(f'Unknown IR Assign: {ir_assign}')
# #     return x86_stmnts

# # def to_x86_expr(ir_expr: ir_Expr) -> List[x86_stmnt]:
# #     '''
# #     Convert IR Expr to x86
# #     '''
# #     assert(isinstance(ir_expr, ir_Expr))
# #     x86_stmnts = []
# #     if isinstance(ir_expr.value, ir_Call):
# #         x86_stmnts.extend(to_x86_call(ir_expr.value))
# #     else:
# #         raise Exception(f'Unknown IR Expr: {ir_expr}')
# #     return x86_stmnts

# # def to_x86_return(ir_return: ir_Return) -> List[x86_stmnt]:
# #     '''
# #     Convert IR Return to x86
# #     '''
# #     assert(isinstance(ir_return, ir_Return))
# #     return [x86_Ret()]

# # def to_x86_call(ir_call: ir_Call) -> List[x86_stmnt]:
# #     '''
# #     Convert IR Call to x86
# #     '''
# #     assert(isinstance(ir_call, ir_Call))
# #     # return [x86_Call(ir_call.target)]
# #     return [x86_Call('print_int_nl')]
"""
# Purpose: Define a type system to represent flat x86 Intermediate representation
    IR_Variable(name: str, neighbors: [], location: [IR_Register | IR_MemoryLocation], allow_spill: bool)
    IR_Register(name: str, caller_saved: bool)
    IR_MemoryLocation(name: str, offset: int, base: Register)
    IR_Module(statements: [IR_Statement])
    IR_Statement(type: str, live_variables: [IR_Variable])
"""

import ast

from dataclasses import dataclass
from io import StringIO
import sys
from typing import List, MutableSet, Union
from pprint import pprint

from tree_utils import TempContext

# from cfg import CFG

TAB_PREF = '    '
VAR_SIZE = 8

@dataclass
class IR_Constant():
    value: int

    def __str__(self):
        return self.print()

    def print(self, x86=False):
        return f'${self.value}'

class IR_Register():
    def __init__(self, name: str, caller_saved: bool = False, neighbors: MutableSet[Union['IR_Variable', 'IR_Register']] = None):
        self.name = name
        self.caller_saved = caller_saved
        self.priority = 0 if caller_saved else 1
        self.neighbors = set() if neighbors is None else neighbors
        # Used for saving registers accross function calls
        self.is_used = False

    def __repr__(self):
        return f'{self.name}'

    def __str__(self):
        return self.print()

    def print(self, x86=False):
        return f'{self.name}'


# x86 8 bit Registers
IR_REG_AL = IR_Register(r'%al', True)
# x86 32 bit Registers
IR_REG_RAX = IR_Register(r'%rax', True)
IR_REG_RBX = IR_Register(r'%rbx', False)
IR_REG_RCX = IR_Register(r'%rcx', True)
IR_REG_RDX = IR_Register(r'%rdx', True)
IR_REG_RSI = IR_Register(r'%rsi', True) # This register should be caller saved, but it's making weird issues
IR_REG_RDI = IR_Register(r'%rdi', True) # This register is not caller saved, but we treat it as such for now
IR_REG_R8 = IR_Register(r'%r8', True)
IR_REG_R9 = IR_Register(r'%r9', True)
IR_REG_R10 = IR_Register(r'%r10', True)
IR_REG_R11 = IR_Register(r'%r11', True)
IR_REG_R12 = IR_Register(r'%r12', False)
IR_REG_R13 = IR_Register(r'%r13', False)
IR_REG_R14 = IR_Register(r'%r14', False)
IR_REG_R15 = IR_Register(r'%r15', False)
## Other Registers (Stack)
# TODO: change these to callee saved (and double check)
IR_REG_RBP = IR_Register(r'%rbp', True)
IR_REG_RSP = IR_Register(r'%rsp', True)
x86_color_registers = set([IR_REG_RAX,
	IR_REG_RBX,
	IR_REG_RCX,
	IR_REG_RDX,
	# IR_REG_RSI,
	IR_REG_RDI,
	IR_REG_R8,
	IR_REG_R9,
	IR_REG_R10,
	IR_REG_R11,
	IR_REG_R12,
	IR_REG_R13,
	IR_REG_R14,
	IR_REG_R15,
	])

class IR_MemoryLocation():
    def __init__(self, name: str, offset: int, base: Union['IR_Variable', IR_Register]):
        self.name = name
        self.offset = offset
        self.base = base

    def __str__(self):
        return self.print()

    def print(self, x86=False):
        return f'{self.offset}({self.base.print(x86=x86)})'

class IR_Variable():
    def __init__(self, name: str, neighbors: MutableSet[Union['IR_Variable', IR_Register]] = None, illegal_locations: MutableSet[Union[IR_Register, IR_MemoryLocation]] = None, location: list[Union[IR_Register, IR_MemoryLocation]] = None, allow_spill: bool = False):
        self.name = name
        self.neighbors = set() if neighbors is None else neighbors
        self.illegal_locations = set() if illegal_locations is None else illegal_locations
        self.location = location
        self.allow_spill = allow_spill
        

    def __repr__(self):
        return f'{self.name}'

    def __str__(self):
        return self.print()

    def print(self, x86=False):
        if x86:
            if self.location is None:
                return f'{self.name}'
            return f'{self.location}'
        return f'{self.name}'

class IR_Statement():
    # Statement types
    MOVE = 'mov'
    ADD = 'add'
    SUB = 'sub'
    NEG = 'neg'
    PUSH = 'push'
    POP = 'pop'
    RET = 'ret'
    CALL = 'call'
    DIRECTIVE_GLOBAL = '.global'
    LABEL = 'LABEL'
    JUMP = 'jmp'  # jmp label
    JUMPEQ = 'je'  # je label
    JUMPNE = 'jne'  # jne label
    CMP = 'cmp'  # cmpl %eax, %ebx 
    SETEQ = 'sete'  # sete %al
    SETNE = 'setne'  # setne %al
    MOVZBL = 'movzb'  # movzbl %al, %eax


    n_args_map = {
        MOVE: 2,
        ADD: 2,
        SUB: 2,
        NEG: 1,
        PUSH: 1,
        POP: 1,
        RET: 0,
        CALL: -1,
        DIRECTIVE_GLOBAL: -1,
        LABEL: -1,
        JUMP: -1,
        JUMPEQ: -1,
        JUMPNE: -1,
        CMP: 2,
        SETEQ: 1,
        SETNE: 1,
        MOVZBL: 2
    }

    indent_map = {
        MOVE: 1,
        ADD: 1,
        SUB: 1,
        NEG: 1,
        PUSH: 1,
        POP: 1,
        RET: 1,
        CALL: 1,
        DIRECTIVE_GLOBAL: 0,
        LABEL: 0,
        JUMP: 1,
        JUMPEQ: 1,
        JUMPNE: 1,
        CMP: 1,
        SETEQ: 1,
        SETNE: 1,
        MOVZBL: 1
    }

    def __init__(self, type: str, src: Union[IR_Constant, IR_Variable] = None, dest: Union[IR_Constant, IR_Variable] = None, str_arg: str = None, comment: str = None):
        self.type = type
        self.src = src
        self.dest = dest
        self.str_arg = str_arg
        self.live_variables = set()
        self.comment = comment
        self.src_lvn = None
        self.dest_lvn = None
        self.op_lvn = None

    def __repr__(self):
        return f'{self.type} {self.src} {self.dest} {self.str_arg}'

    def __str__(self):
        return self.print()

    def print(self, x86=False):
        # Some statements have a different format
        # negl, push, pop has only one operand
        n_args = IR_Statement.n_args_map[self.type]
        s_src = self.src.print(x86=x86) if self.src is not None else None
        s_dest = self.dest.print(x86=x86) if self.dest is not None else None
        s_type = self.type
        indent = TAB_PREF * IR_Statement.indent_map[self.type]
        # if n_args == -2:
            # # Must remove the colon from the label
            # if self.type == IR_Statement.JUMP or self.type == IR_Statement.JUMPEQ or self.type == IR_Statement.JUMPNE:
            #     return f'{indent}{s_type} {self.str_arg[:-1]}'
            # return f'{indent}{s_type} {s_src}'
        if n_args == -1:
            if self.type == IR_Statement.LABEL:
                return f'{indent}{self.str_arg}:'
            return f'{indent}{s_type} {self.str_arg}'
        if n_args == 0:
            return f'{indent}{s_type}'
        if n_args == 1:
            return f'{indent}{s_type} {s_src}'
        if n_args == 2:
            return f'{indent}{s_type} {s_src}, {s_dest}'
        # TODO: Print comments
        raise Exception(f'Invalid number of arguments for statement type {s_type}')

# @dataclass
# class IR_FunctionCall():
#     name: str
#     args: list[Union[IR_Constant, IR_Variable]] = field(default_factory=list)
#     dest: Union[IR_Constant, IR_Variable] = None
#     live_variables: MutableSet[Union['IR_Variable', IR_Register]] = field(default_factory=set)

#     def __str__(self):
#         return f'{TAB_PREF}call {self.name}'

#     def print_x86(self):
#         return str(self)

class IR_Function(TempContext):
    def __init__(self, function_name: str = "main", statements: List[IR_Statement] = [], variables: MutableSet[IR_Variable] = []):
        self.statements = statements
        self.variables = variables
        # self.registers: MutableSet[IR_Register] = registers
        # This number can be used to allocate space on the stack at function entry
        self.stack_size = 0
        self.temp_num = 0

    def _create_spill_variable(self):
        v = IR_Variable(f's{self.temp_num}')
        self.variables.add(v)
        self.temp_num += 1
        return v

    def _create_spill_memory(self):
        v = IR_MemoryLocation(f's{self.stack_size}', -4 * (self.stack_size + 1), IR_REG_RBP)
        self.stack_size += 1
        return v

    def assign_homes(self):
        new_statements = []
        # Assign return variables to all of the function calls
        for statement in self.statements:
            if statement.type == IR_Statement.CALL:
                # If there are function arguments, push them onto the stack in reverse order
                if statement.src is not None:
                    # new_statements.append(IR_Statement(IR_Statement.PUSH, statement.src))
                    # x86_64 calling convention
                    new_statements.append(IR_Statement(IR_Statement.MOVE, statement.src, IR_Variable(IR_REG_RDI)))
                new_statements.append(statement)
                # Return value is in EAX, move it to the destination
                if statement.dest is not None:
                    new_statements.append(IR_Statement(IR_Statement.MOVE, IR_Variable(IR_REG_RAX), statement.dest))
            # elif statement.type == IR_Statement.NEG:
            #     new_statements.append(IR_Statement(IR_Statement.MOVE, statement.src, statement.dest))
            #     statement.src = statement.dest
            #     new_statements.append(statement)
            else:
                new_statements.append(statement)
        self.statements = new_statements

    def delete_dead_code(self):
        # Iterate through all of the statements and delete the dead ones
        # A statement is dead if it is a move from the same
        # src memory location to the same dest memory location
        for statement in self.statements:
            # Check the type of the statement
            if statement.type == IR_Statement.MOVE:
                # Skip if the src is a constant since this makes the condition impossible
                # (dest cannot be a constant)
                if isinstance(statement.src, IR_Constant):
                    continue
                if statement.src.location == statement.dest.location:
                    # Dead code
                    print("Dead code")
                    print(statement)
                    self.statements.remove(statement)

    def print_structure(self, indent=1, stream=None):
        pprint(self.statements, indent=indent, stream=stream)

    def print_colors(self, stream=sys.stdout):
        for var in self.variables:
            stream.write(f'{var.__repr__()}: {var.location}\n')

    def print_interference_graph(self, stream=sys.stdout):
        stream.write(f'// INTERFERENCE GRAPH\n')
        for var in self.variables:
            stream.write(f'// {var}: {var.neighbors}\n')
        for reg in self.registers:
            if len(reg.neighbors) == 0:
                continue
            stream.write(f'// {reg}: {reg.neighbors}\n')
    
    def print(self, x86 = False, print_comments=True, print_liveness=False, print_interference=False, stream=sys.stdout):
        if x86:
            # Add the main label and function prologue (ABI) statements
            prologue = [
                IR_Statement(IR_Statement.DIRECTIVE_GLOBAL, str_arg='main'),
                IR_Statement(IR_Statement.LABEL, str_arg='main'),
                # IR_Comment('Function prologue'),
                IR_Statement(IR_Statement.PUSH, IR_Variable(IR_REG_RBP)),
            ]
            prologue += [IR_Statement(IR_Statement.MOVE, IR_Variable(IR_REG_RSP), IR_Variable(IR_REG_RBP)),]
            # Push all of the callee-saved registers which are used in the program
            saved_regs = []
            for reg in self.registers:
                if not reg.is_used:
                    if not reg.caller_saved:
                        saved_regs.append(IR_Statement(IR_Statement.PUSH, IR_Variable(reg)))
            prologue += saved_regs
            # allocate stack space if necessary
            # TODO: This should be done in the register allocator
            # Determine the stack space needed for the function rounding up to a multiple of 16
            print(f'Stack size: {self.stack_size} bytes')
            print(f'saved_regs: {len(saved_regs)}')
            # self.stack_size = ((self.stack_size * VAR_SIZE + VAR_SIZE * len(saved_regs)) + 15) & ~15
            self.stack_size = (((self.stack_size * VAR_SIZE) + 15) & ~15) + (VAR_SIZE * (len(saved_regs)) % 16)
            print(f'Stack size: {self.stack_size} bytes')
            if self.stack_size > 0:
                prologue.append(IR_Statement(IR_Statement.SUB, IR_Constant(self.stack_size), IR_Variable(IR_REG_RSP)))
            # prepend to statement list
            self.statements = prologue + self.statements
            # Add the function epilogue (ABI) statements
            epilogue = [
                # IR_Comment('Function epilogue'),
                IR_Statement(IR_Statement.MOVE, IR_Constant(0), IR_Variable(IR_REG_RAX), comment='Return 0'),
            ]
            # Pop all of the callee-saved registers which are used in the program
            for reg in reversed(saved_regs):
                epilogue.append(IR_Statement(IR_Statement.POP, reg.src))
            epilogue += [
                IR_Statement(IR_Statement.MOVE, IR_Variable(IR_REG_RBP), IR_Variable(IR_REG_RSP)),
                IR_Statement(IR_Statement.POP, IR_Variable(IR_REG_RBP)),
                IR_Statement(IR_Statement.RET),
            ]
            # append to statement list
            self.statements = self.statements + epilogue
        # Print all the statements to the given stream
        for statement in self.statements:
            if print_liveness:
                if isinstance(statement, IR_Statement):
                    s = str(statement.live_variables) if len(statement.live_variables) > 0 else '{}'
                    stream.write(f'{TAB_PREF}// {s}\n')
            if print_comments and statement.comment is not None:
                stream.write(TAB_PREF + f'// {statement.comment}\n')
            s_stmnt = statement.print(x86=x86)
            stream.write(s_stmnt)
            stream.write('\n')
        if print_interference:
            stream.write('\n\n')
            self.print_interference_graph(stream=stream)

    def __str__(self):
        str = StringIO()
        self.print_structure(stream=str)
        return str.getvalue()

    def optimize(self):
        # Local Value Numbering
        # 1. For each statement, get the value number of src and destination operands
        # 2. Construct a hash key from the value numbers of the operands and the statement type
        # 3. If the hash key is in the hash table, associate the statement with the value number
        # 4. If the hash key is not in the hash table, add it and associate the statement with the value number
        print('Optimizing...')
        hash_table = {}
        curr_val_num = 0
        optimized_flag = False
        for statement in self.statements:
            #reset lvn values
            statement.src_lvn = None
            statement.dest_lvn = None


        for statement in self.statements:
            print(hash_table)
            # Get the value numbers of the operands
            src_val_num = None
            dest_val_num = None
            if statement.type == IR_Statement.MOVE:
                src_val_num = hash_table.get(statement.src.print())
                if src_val_num is None:
                    src_val_num = curr_val_num
                    hash_table[statement.src.print()] = curr_val_num
                    curr_val_num += 1
                statement.src_lvn = src_val_num 
                statement.dest_lvn = src_val_num
                hash_table[statement.dest.print()] = src_val_num
            
            elif statement.type == IR_Statement.ADD:
                src_val_num = hash_table.get(statement.src.print())
                if src_val_num is None:
                    src_val_num = curr_val_num
                    hash_table[statement.src.print()] = curr_val_num
                    curr_val_num += 1
                dest_val_num = hash_table.get(statement.dest.print())
                if dest_val_num is None:
                    dest_val_num = curr_val_num
                    hash_table[statement.dest.print()] = curr_val_num
                    curr_val_num += 1
                hash_key_op = str((statement.type, src_val_num, dest_val_num))
                op_num = hash_table.get(hash_key_op)
                if op_num is None:
                    op_num = curr_val_num
                    hash_table[hash_key_op] = curr_val_num
                    curr_val_num += 1
                hash_table[statement.dest.print()] = op_num
                statement.src_lvn = src_val_num
                statement.dest_lvn = dest_val_num
                statement.op_lvn = op_num

            elif statement.type == IR_Statement.NEG:
                dest_val_num = hash_table.get(statement.src.print())
                if dest_val_num is None:
                    dest_val_num = curr_val_num
                    hash_table[statement.dest.print()] = curr_val_num
                    curr_val_num += 1
                hash_key_op = str((statement.type, dest_val_num))
                op_num = hash_table.get(hash_key_op)
                if op_num is None:
                    op_num = curr_val_num
                    hash_table[hash_key_op] = curr_val_num
                    curr_val_num += 1
                statement.dest_lvn = op_num
                hash_table[statement.src.print()] = op_num
        
        return hash_table

        # apply constant folding
        for statement in self.statements:
            if statement.type == IR_Statement.ADD:
                if isinstance(statement.src, IR_Constant):
                    key = is_constant(statement.dest_lvn, hash_table)
                    if key:
                        print('found constant folding')
                        print(statement)
                        const_val = int(statement.src.value) + int(key[1:])
                        print(const_val)
                        statement.type = IR_Statement.MOVE
                        statement.src = IR_Constant(const_val)
                        statement.dest_lvn = statement.src_lvn
                        optimized_flag = True
                        break
                
                elif isinstance(statement.src, IR_Variable):
                    key = is_constant(statement.src_lvn, hash_table)
                    if key:
                        print('found constant folding')
                        print(statement)
                        print(key[1:])
                        const_val = int(key[1:])
                        #print(const_val)
                        statement.src = IR_Constant(const_val)
                        statement.dest = statement.dest
                        statement.dest_lvn = statement.src_lvn
                        optimized_flag = True
                        break

        return optimized_flag

       
        


# Useful functions
def print_IR_Module(module: IR_Function):
    for statement in module.statements:
        # print all names and members of a dataclass
        print(statement.__dict__)
    
def is_constant(num_var, dict):
    for key in dict:
        if (key[0] == '$') and (dict[key]==num_var):
            return key
    return False

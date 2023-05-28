from typing import List
from IR import *



# Control flow graph class
# This class is used to represent the control flow graph of a function
# It is used to generate the liveness analysis and interference graph
# It is also used to generate the x86 assembly code
# It is a directed graph with nodes being basic blocks of statements
# and edges being the control flow between the basic blocks and liveness variables
# The graph is represented as a dictionary of basic blocks
# Each basic block is a list of statements
# Each statement is a dataclass with the following fields:
# reference to IR_Statement objects in an ordered list of statements
# reference to the next basic block based on the control flow
# reference to the previous basic block based on the control flow

class CFG:
    '''
    Control flow graph class:
    This class is used to represent the control flow graph of a function.
    Vertices are basic blocks of statements.
    Edges are the control flow between the basic blocks and liveness variables.
    '''
    class BasicBlock:
        def __init__(self, statements: List[ir_stmt], jmp_name: str , jmp_type: str, label: str):
            self.statements = statements
            # self.live_variables = set()
            # self.live_visited = False
            self.label = label
            self.jmp_type = jmp_type
            self.jmp_name = jmp_name
            self.entry = None
            self.exit = None
            self.next_blocks = set()
            self.prev_blocks = set()

        def add_next_block(self, block):
            self.next_blocks.add(block)

        def add_prev_block(self, block):
            self.prev_blocks.add(block)

        def get_next_blocks(self):
            return self.next_blocks
        
        def get_prev_blocks(self):
            return self.prev_blocks

        def print(self, file=sys.stdout):
            print_ir(self.statements, file=file)

        def __repr__(self):
            return f'BasicBlock({self.label})'

        def __str__(self):
            str = StringIO()
            self.print(stream=str)
            return str.getvalue()

    def __init__(self, function: ir_Function):
        self.basic_blocks = []
        self.block_dict = {}
        self.variables = dict()
        self._create_basic_blocks(function)

    def _create_basic_blocks(self, function: ir_Function):
        '''
        From an ir_Function, construct all vertices (no edges) by iterating through ir_stmnt's
        '''
        # label = function.name
        # statements = []

        # def add_block(statements, label):
        #     block = CFG.BasicBlock(statements, None, None, label)
        #     self.basic_blocks.append(block)
        #     self.block_dict[label] = block

        # for statement in function.body:
        #     if isinstance(statement, ir_Label):
        #         if statements:
        #             self.add_basic_block(statements, label)
        #             statements = []
        #         label = statement.name
        #     elif isinstance(statement, ir_Jump):
        #         statements.append(statement)
        #         self.add_basic_block(statements, label, jmp_name=statement.name, jmp_type='jump')
        #         statements = []
        #     elif isinstance(statement, ir_CJump):
        #         statements.append(statement)
        #         self.add_basic_block(statements, label, jmp_name=statement.true_name, jmp_type='cjump')
        #         statements = []
        #     else:
        #         statements.append(statement)

    def get_entry_block(self):
        return self.basic_blocks[0]
    
    def get_exit_block(self):
        return self.basic_blocks[-1]

    def _get_block(self, label: str):
        for block in self.basic_blocks:
            if block.label == label:
                return block
        return None

    # Add a basic block to the CFG with the given statement list
    def add_basic_block(self, statements: list[IR_Statement], label: str = None, entry: bool = False, exit: bool = False, jmp_name: str = None , jmp_type: str = None):
        block = BasicBlock(statements, label = label, entry = entry, exit = exit, jmp_name = jmp_name, jmp_type =jmp_type)
        self.basic_blocks.append(block)
        if entry:
            self.entry_block = block
        if exit:
            self.exit_block = block
        return block
    
    def get_block_label(self, block: BasicBlock):
        for statement in block.statements:
            if statement.type == IR_Statement.LABEL:
                return statement.str_arg
        return None


    # Goes through Module and creates a CFG
    def create_CFG(self):
        #Adds statements to a list until a jump is found
        #Then adds the list to a new basic block and clears the list
        self.basic_blocks = []
        self.block_dict = {}
        self.variables = dict()
        statements = []
        entry = True
        label = 'entry'
        label_true = True
        for statement in module.statements:
            # if isinstance(statement.src, IR_Variable):
            #     if statement.src not in self.variables:
            #         self.variables[statement.src.name] = statement.src
            # if isinstance(statement.dest, IR_Variable):
            #     if statement.dest not in self.variables:
            #         self.variables[statement.dest.name] = statement.dest
            if statement.type == IR_Statement.LABEL:
                if label_true:
                    self.add_basic_block(statements, label=label, entry=entry)
                    statements = []
                    entry = False
                    label_true = False
                    label = statement.str_arg
                else:
                    label = statement.str_arg
                    label_true = True
            statements.append(statement)
            if statement.type == IR_Statement.JUMP:
                #if jump is jmp, dont add a new basic block as next block
                #print(statement.src)
                self.add_basic_block(statements, label=label, entry=entry, jmp_name=statement.str_arg, jmp_type=statement.type)
                statements = []
                entry = False
                label_true = False
            elif statement.type == IR_Statement.JUMPEQ:
                #if jump is jumpeq, add a new basic block as next block
                self.add_basic_block(statements, label=label, entry=entry, jmp_name=statement.str_arg, jmp_type=statement.type)
                statements = []
                entry = False
                label_true = False
            elif statement.type == IR_Statement.JUMPNE:
                #if jump is jumpne, add a new basic block as next block
                self.add_basic_block(statements, label=label, entry=entry, jmp_name=statement.str_arg, jmp_type=statement.type)
                statements = []
                entry = False
                label_true = False
        #Adds the last list of statements to a basic block
        self.add_basic_block(statements, label=label, exit=True)
        #Sets the next and previous blocks for each basic block


        for i, block in enumerate(self.basic_blocks):
            if block.jmp_type == IR_Statement.JUMP:
                for b in self.basic_blocks:
                    # print(b.label, " ", block.jmp_name)
                    if b.label == block.jmp_name:
                        block.next_blocks.append(b)
                        b.prev_blocks.append(block)
            elif block.jmp_type == IR_Statement.JUMPEQ:              
                for b in self.basic_blocks:
                    if b.label == block.jmp_name:
                        block.next_blocks.append(b)
                        b.prev_blocks.append(block)
                # also add the next block as the next block
                block.next_blocks.append(self.basic_blocks[i + 1])
                self.basic_blocks[i + 1].prev_blocks.append(block)
            elif block.jmp_type == IR_Statement.JUMPNE:
                for b in self.basic_blocks:
                    if b.label == block.jmp_name:
                        block.next_blocks.append(b)
                        b.prev_blocks.append(block)
                # also add the next block as the next block
                block.next_blocks.append(self.basic_blocks[i + 1])
                self.basic_blocks[i + 1].prev_blocks.append(block)
            elif not block.exit:
                # if no jump, add the next block as the next block
                block.next_blocks.append(self.basic_blocks[i + 1])
                self.basic_blocks[i + 1].prev_blocks.append(block)

        print('\n\nBasic Blocks: ')
        for block in self.basic_blocks:
            print(block.label)
            block.print()
            print(block.next_blocks)
            print(block.prev_blocks)
            print(block.jmp_name)
            print('\n')



        # Create a block dictionary indexed by it's label
        self.block_dict = { label: block for block in self.basic_blocks }
        

    # MOVE = 'movl'
    # ADD = 'addl'
    # SUB = 'subl'
    # NEG = 'negl'
    # PUSH = 'pushl'
    # POP = 'popl'
    # RET = 'ret'
    # CALL = 'call'
    # DIRECTIVE_GLOBAL = '.global'
    # LABEL = 'LABEL'
    # JUMP = 'jmp'  # jmp label
    # JUMPEQ = 'je'  # je label
    # JUMPNE = 'jne'  # jne label
    # CMP = 'cmpl'  # cmpl %eax, %ebx 
    # SETEQ = 'sete'  # sete %al
    # SETNE = 'setne'  # setne %al
    # MOVZBL = 'movzbl'  # movzbl %al, %eax

        
# def IR_get_read_write_sets(stmnt: IR_Statement):
#     """
#     Return (read set, write set) tuple"""
#     s = [[], []]
#     if stmnt.type == IR_Statement.MOVE:
#         s = [[stmnt.src], [stmnt.dest]]
#     if stmnt.type == IR_Statement.ADD:
#         s = [[stmnt.src, stmnt.dest], [stmnt.dest]]
#     if stmnt.type == IR_Statement.SUB:
#         s = [[], []]
#     if stmnt.type == IR_Statement.NEG:
#         s = [[stmnt.src], [stmnt.dest]]
#     if stmnt.type == IR_Statement.PUSH:
#         s = [[stmnt.src], []]
#     if stmnt.type == IR_Statement.POP:
#         s = [[], [stmnt.dest]]
#     if stmnt.type == IR_Statement.CALL:
#         s = [[stmnt.src], [stmnt.dest]]
#     if stmnt.type == IR_Statement.CMP:
#         s = [[stmnt.src, stmnt.dest], []]
#     if stmnt.type == IR_Statement.MOVZBL:
#         s = [[stmnt.src], [stmnt.dest]]
#     # Filter out IR_Constants and IR_Registers
#     s[0] = [x for x in s[0] if isinstance(x, IR_Variable)]
#     s[1] = [x for x in s[1] if isinstance(x, IR_Variable)]
#     s = (set(s[0]), set(s[1]))
#     return s

# def LivenessAnalysis(cfg: CFG):
#     # Reset the live set for each block
#     for block in cfg.basic_blocks:
#         block.live_variables = set()
#         block.live_visited = False
#         for statement in block.statements:
#             statement.live_variables = set()
#     # Start with the end block
#     # The live set is empty
#     block = cfg.exit_block
#     _liveness(block, set())


# def _liveness(block: BasicBlock, live_in: set):
#     block.live_visited = True
#     # For each statement in the block
#     for statement in reversed(block.statements):
#         #statement.print()
#         live_in = live_in.copy()
#         read_set, write_set = IR_get_read_write_sets(statement)
#         # L_before = (L_after - W) U R
#         live_in = (live_in - write_set) | read_set
#         statement.live_variables = live_in
#     # When we get to the top of the block, we need to propagate the live set to the previous blocks
#     # unless the live set is the same as the previous block
#     for prev_block in block.prev_blocks:
#         if not (prev_block.live_variables == live_in and prev_block.live_visited):
#             prev_block.live_variables = live_in | prev_block.live_variables
#             _liveness(prev_block, prev_block.live_variables)

# # check %al for interferences since its %eax
# def Interference_graph(cfg: CFG):
#     # adds all statements to a list
#     statements = []
#     registers = x86_color_registers
#     for block in cfg.basic_blocks:
#         for statement in block.statements:
#             statements.append(statement)

#     # Add all unique variables and registers to the CFG variables dictionary
#     # TODO: Populate the variables list some other way, this leads to an error
#     # when a variable is assigned but never used...
#     # We could delete statements like this as an optimization but for now it's causing
#     # and error with the compiler
#     for statement in statements:
#         if isinstance(statement.src, IR_Variable):
#             if statement.src not in cfg.variables:
#                 cfg.variables[statement.src.name] = statement.src
#         if isinstance(statement.dest, IR_Variable):
#             if statement.dest not in cfg.variables:
#                 cfg.variables[statement.dest.name] = statement.dest
            
#         # for variable in statement.live_variables:
#         #     if variable not in cfg.variables:
#         #         cfg.variables[variable.name] = variable
#     for register in registers:
#         if register not in cfg.variables:
#             cfg.variables[register.name] = register


#     for i, statement in enumerate(statements):
#             # Get liveness of next statement (empty set if this is the last statement)
#             next_live = set() if i == len(statements) - 1 else statements[i + 1].live_variables
#             # Check the statement type
#             # Check the type of the statement
#             if statement.type == IR_Statement.MOVE:
#                 # The dest interferes with all variables live after the statement, except the src
#                 for var in next_live:
#                     # (except the src)
#                     if isinstance(statement.src, IR_Variable) and var == statement.src:
#                         continue
#                     # ignore if the variable is the same as the destination
#                     if var == statement.dest:
#                         continue
#                     # add intereference edge self (dest)
#                     cfg.variables[statement.dest.name].neighbors.add(var)
#                     # add intereference edge to neighbor
#                     cfg.variables[var.name].neighbors.add(statement.dest)
#             elif statement.type == IR_Statement.ADD:
#                 # the dest interferes with all variables live after the statement
#                 for var in next_live:
#                     # ignore if the variable is the same as the destination
#                     if var == statement.dest:
#                         continue
#                     # add intereference edge self (dest)
#                     cfg.variables[statement.dest.name].neighbors.add(var)
#                     # add intereference edge to neighbor
#                     cfg.variables[var.name].neighbors.add(statement.dest)
#             elif statement.type == IR_Statement.CALL:
#                 # Caller saved registers interfere with all variables live after the statement
#                 for var in next_live:
#                     for reg in registers:
#                         if reg.caller_saved:
#                             # Add interference edge to register
#                             #reg.neighbors.neighbors.add(var)
#                             cfg.variables[reg.name].neighbors.add(var)
#                             # Add interference edge to varaible
#                             #var.neighbors.neighbors.add(reg)
#                             cfg.variables[var.name].neighbors.add(reg)
#                     if isinstance(statement.dest, IR_Variable):
#                         if var == statement.dest:
#                             continue
#                         # add intereference edge self (dest)

#                         cfg.variables[statement.dest.name].neighbors.add(var)
#                                     #var.neighbors.neighbors.add(statement.dest)
#                         cfg.variables[var.name].neighbors.add(statement.dest)
#             elif statement.type == IR_Statement.CMP:
#                 for var in next_live:
#                     #if isinstance(statement.src, IR_Variable) and var == statement.src:
#                     #    continue
#                     #if isinstance(statement.dest, IR_Variable) and var == statement.dest:
#                     #    continue
#                     # add intereference edge self (dest)
#                     cfg.variables[IR_REG_RAX.name].neighbors.add(var)
#                     # add intereference edge to neighbor
#                     cfg.variables[var.name].neighbors.add(IR_REG_RAX)
#             elif statement.type == IR_Statement.MOVZBL:
#                 # The dest interferes with all variables live after the statement, except the src
#                 for var in next_live:
#                     if isinstance(statement.src, IR_Variable) and var == statement.src:
#                         continue
#                     # ignore if the variable is the same as the destination
#                     if var == statement.dest:
#                         continue
#                     # add intereference edge self (dest)
#                     cfg.variables[statement.dest.name].neighbors.add(var)
#                     # add intereference edge to neighbor
#                     cfg.variables[var.name].neighbors.add(statement.dest)
#             elif statement.type == IR_Statement.SETEQ:
#                 for var in next_live:
#                     #if isinstance(statement.src, IR_Variable) and var == statement.src:
#                     #    continue
#                     #if isinstance(statement.dest, IR_Variable) and var == statement.dest:
#                     #    continue
#                     # add intereference edge self (dest)
#                     cfg.variables[IR_REG_RAX.name].neighbors.add(var)
#                     # add intereference edge to neighbor
#                     cfg.variables[var.name].neighbors.add(IR_REG_RAX)
#             elif statement.type == IR_Statement.SETNE:
#                 for var in next_live:
#                     #if isinstance(statement.src, IR_Variable) and var == statement.src:
#                     #    continue
#                     #if isinstance(statement.dest, IR_Variable) and var == statement.dest:
#                     #    continue
#                     # add intereference edge self (dest)
#                     cfg.variables[IR_REG_RAX.name].neighbors.add(var)
#                     # add intereference edge to neighbor
#                     cfg.variables[var.name].neighbors.add(IR_REG_RAX)
#             elif statement.type == IR_Statement.NEG:
#                 # for var in next_live:
#                 # Make sure src interferes with dest
#                 # unless src is a constant
#                 if isinstance(statement.src, IR_Variable) and isinstance(statement.dest, IR_Variable):
#                     var = statement.src
#                     # ignore if the variable is the same as the destination
#                     if var != statement.dest:
#                         # add intereference edge self (dest)
#                         cfg.variables[statement.dest.name].neighbors.add(var)
#                         # add intereference edge to neighbor
#                         cfg.variables[var.name].neighbors.add(statement.dest)
                    
#             """for variable in statement.live_variables:
#                     if variable not in cfg.variables:
#                         cfg.variables[variable] = set()
#                     for other_variable in statement.live_variables:
#                         if variable != other_variable:
#                             cfg.variables[variable].add(other_variable)"""

#     print('Variable Dictionary')
#     for key, value in cfg.variables.items():
#         print(key, value, id(value))

#     return cfg.variables


# class variable_idk_why_another:
#     def __init__(self, name, neighbors):
#         self.name = name
#         self.locations = None
#         self.neighbors = neighbors
#         self.illegal_locations = set()


# # assign registers to variables
# def color_graph(IR: IR_Function, cfg: CFG):
#     # Reconstruct the list of variables based on the statement list
#     IR.variables = set()
#     for statement in IR.statements:
#         print("stmnt: ", statement.__repr__())
#         if isinstance(statement.dest, IR_Variable):
#             print("ADD_VAR: ", statement.dest.__repr__(), " ", id(statement.dest))
#             IR.variables.add(statement.dest)
#         if isinstance(statement.src, IR_Variable):
#             print("ADD_VAR: ", statement.src.__repr__(), " ", id(statement.src))
#             IR.variables.add(statement.src)
#     # Cleanup the variable locations
#     print("VARIABLES: ", IR.variables)
#     # raise RuntimeError("jklasdhfjkshdf")
#     for var in IR.variables:
#         print("VARS: ", var.name, id(var), var.neighbors)
#         # raise RuntimeError("jklasdhfjkshdf")
#         var.location = None
#         var.illegal_locations = set()
#     print("after")
#     # Prepopulate the illegal_locations of each variable by looking at the neighbors of the registers
#     for reg in IR.registers:
#         for neighbor in reg.neighbors:
#             neighbor.illegal_locations.add(reg)
#     # Sort the variables by degree
#     variables = IR.variables.copy()
#     # sort the registersby their priority
#     IR.registers = sorted(IR.registers, key=lambda reg: reg.priority)
#     # print('Sorted registers:', list(zip(IR.registers, [var.priority for var in IR.registers])))
#     # Iterate through the variables and assign them a register
#     # Color a variable with the lowest degree first
#     # - If there are no available registers, then spill the variable
#     # Update its neighbors illegal_locations set
#     # Pick the next variable to color
#     # - Should we resort the variables list after popping the last one that's colored?
#     while len(variables) > 0:
#         # Theres more variables to color
#         # Sort the variables
#         variables = sorted(list(variables), key=lambda var: len(var.illegal_locations), reverse=True)
#         # print('Sorted variables:', list(zip(variables, [len(var.illegal_locations) for var in variables])))
#         var = variables.pop(0)
#         # print(var)
#         # need to color var
#         reg = None
#         for r in IR.registers:
#             if r not in var.illegal_locations:
#                 reg = r
#                 break
#         if reg is None:
#             # No available registers
#             # Spill the variable
#             spill_loc = IR._create_spill_memory()
#             var.location = spill_loc
#             print('Spilling variable:', var, var.location, var.illegal_locations)
#         else:
#             # Assign the register to the variable
#             var.location = reg
#             # Update the neighbors illegal_locations set
#             for neighbor in var.neighbors:
#                 if isinstance(neighbor, IR_Variable):
#                     neighbor.illegal_locations.add(reg)

#     # Coloring is done, loop through all statements and find illegal instructions
#     # e.g. movl -4($ebp), -8(%ebp) is illegal since it has more than one memory operand
#     # if we find an illegal statement, insert spill statments with new temprary variables
#     spilled = False
#     for i, statement in enumerate(IR.statements):
#         # Ignore statements which cannot have illegal memory accesses
#         if statement.type not in [IR_Statement.MOVE, IR_Statement.ADD, IR_Statement.CMP]:
#             continue
#         # TODO: Spilling is different for addl (addl x, a) spill if a is on the stack
#         print(statement, statement.src, statement.dest)
#         def _spill_helper():
#             spill_var = IR._create_spill_variable()
#             spill_statement = IR_Statement(IR_Statement.MOVE, statement.src, spill_var)
#             # Insert the spill statement before the current statement
#             IR.statements.insert(i, spill_statement)
#             # Update the src of the current statement
#             statement.src = spill_var
#         if statement.type == IR_Statement.CMP:
#             print("Spill cmpl?: ", statement)
#         if statement.type == IR_Statement.CMP:
            
#             if isinstance(statement.dest, IR_Constant):
#                 if isinstance(statement.src, IR_Variable):
#                     # Swap the src and dest
#                     statement.src, statement.dest = statement.dest, statement.src
#                     continue
#                 if isinstance(statement.src, IR_Constant):
#                     # _spill_helper()
#                     # For cmpl, the dest must be a variable
#                     spill_var = IR._create_spill_variable()
#                     spill_statement = IR_Statement(IR_Statement.MOVE, statement.dest, spill_var)
#                     # Insert the spill statement before the current statement
#                     IR.statements.insert(i, spill_statement)
#                     statement.dest = spill_var
#                     spilled = True
#                     continue
#         # skip if the src or dest is a constant
#         if isinstance(statement.src, IR_Constant) or isinstance(statement.dest, IR_Constant):
#             continue
#         if isinstance(statement.src.location, IR_MemoryLocation) and isinstance(statement.dest.location, IR_MemoryLocation):
#             # Turns this:
#             # movl -4(%ebp), -8(%ebp)
#             # into this:
#             # movl -4(%ebp), %eax
#             # movl %eax, -8(%ebp)
#             # Where %eax is a temporary variable
#             # Illegal instruction, spill the src into a temporary variable
#             _spill_helper()
#             spilled = True
#         if statement.type == IR_Statement.MOVZBL and isinstance(statement.dest.location, IR_MemoryLocation):
#             # movzbl %ax, -4(%eax)
#             # is illegal, spill the src into a temporary variable
#             spill_var = IR._create_spill_variable()
#             statement.dest = spill_var
#             spill_statement = IR_Statement(IR_Statement.MOVE, spill_var, statement.dest)
#             IR.statements.insert(i, spill_statement)
#             spilled = True
#     if spilled:
#         print("SPILLED")
#         LivenessAnalysis(cfg)
#         Interference_graph(cfg)
#         color_graph(IR, cfg)

# def constant_folding(IR: IR_Function, cfg: CFG, hash_table):
#     optimized_flag = False
#     for block in cfg.basic_blocks:
#         for statement in block.statements:
#             if statement.type == IR_Statement.ADD:
#                 if isinstance(statement.src, IR_Constant):
#                     key = is_constant(statement.dest_lvn, hash_table)
#                     if key:
#                         print('found constant folding')
#                         print(statement)
#                         const_val = int(statement.src.value) + int(key[1:])
#                         print(const_val)
#                         statement.type = IR_Statement.MOVE
#                         statement.src = IR_Constant(const_val)
#                         statement.dest_lvn = statement.src_lvn
#                         optimized_flag = True
#                         index = IR.statements.index(statement)
#                         IR.statements[index] = statement
#                         break
                
#                 elif isinstance(statement.src, IR_Variable):
#                     key = is_constant(statement.src_lvn, hash_table)
#                     if key:
#                         print('found constant folding')
#                         print(statement)
#                         print(key[1:])
#                         const_val = int(key[1:])
#                         #print(const_val)
#                         statement.src = IR_Constant(const_val)
#                         statement.dest = statement.dest
#                         statement.dest_lvn = statement.src_lvn
#                         optimized_flag = True
#                         index = IR.statements.index(statement)
#                         IR.statements[index] = statement
#                         break

#         return optimized_flag

# def dead_store_elimination(IR: IR_Function, cfg: CFG):
#     for block in cfg.basic_blocks:
#         for statement in block.statements[:-1]:
#             if statement.type == IR_Statement.MOVE:
#                 #if destination is not live after this statement, then remove it
#                 #get next statement live variables
#                 next_statement = block.statements[block.statements.index(statement)+1]
#                 if next_statement:
#                     if not(statement.dest in next_statement.live_variables):
#                         print("next_statement: ", next_statement.live_variables)
#                         print("statement: ", statement.dest)
#                         print(statement.dest in next_statement.live_variables)
#                         block.statements.remove(statement)
#                         IR.statements.remove(statement)
#                         print("Removed statement: ", statement)

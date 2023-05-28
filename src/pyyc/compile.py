#!/bin/env/ python3.10

"""
This is the driver for the python3.10 -> x86 compiler.
"""

import os
# import re
# import io
import sys
from ast import *

from file_utils import getProgramTree
from flatten import *
from desugar import *
from box_front import *
from closure import ClosureTransformer
from x86 import x86_unparse
from to_x86 import *
from tree_utils import *
from to_IR import *
import explicate as exp
# from x86_IR import IR_Function 
# from cfg import *
import P1
import lambda_util

    

def printUsage():
    print(f"Usage: {sys.argv[0]} <input.py>")
    
def compile(path_py):
    print("Compiling", path_py, "to", path_py[:-3] + ".s", end='\n\n')
    # Replace the .py extension with .flatpy and .s respectively
    path_flatpy = path_py[:-3] + '.flatpy'
    path_pyobjpy = path_py[:-3] + '.pyobjpy'
    path_s = path_py[:-3] + '.s'

    # read file as AST and flatten
    tree = getProgramTree(path_py)
    code = unparse(tree)
    print("ORIGINAL:")
    print(code, end='\n\n')

    # print("ORIGINAL AST:")
    # print(dump(tree, indent=2), end='\n\n')

    # Reset the temp generator to start at 0 (and make a new set of user_vars)
    TempContext.temp_gen.reset()

    # ensure the tree is valid P1
    # TODO: add more checks to ensure valid P1
    P1.EnsureValid('P1_').transform(tree)

    # Rename user variables to avoid conflicts with builtins and temps
    renameUserVariables(tree)

    def flatten(tree, num=0):
        old_code = None
        # Need to run until no changes are made
        while old_code != unparse(tree):
            old_code = unparse(tree)
            DesugarUnaryConstantTransformer('u_').transform(tree)
            # Convert Ternary operations into If statements
            tree = DesugarTernaryTransformer(f't{num}_').transform(tree)
            # Convert lambda functions into FunctionDefs
            old_lambda = None
            while old_lambda != unparse(tree):
                old_lambda = unparse(tree)
                tree = DesugarLambdaTransformer(f'lambda{num}_').transform(tree)
                print("LAMBDA:")
            # print(dump(tree, indent=2), end='\n\n')
            # flatten and export as .flatpy for intermediate testing
            tree = FlattenTreeTransformer(f'f{num}_').transform(tree)
            # print(dump(tree, indent=2), end='\n\n') 
            # Convert BoolOp nodes into If statments
            tree = DesguarShortCircuitTransformer(f's{num}_').transform(tree)
            # DesugarTreeTransformer.transform(tree, type="bool")
            tree = FlattenTreeTransformer(f'f{num}_').transform(tree)

    flatten(tree)
    # TODO: constant folding -> evaluate constant conditonals and comparisons
    # TODO: Precompute injections using the constant folding
    tree_flat = "'''\n" + dump(tree, indent=2) + "\n'''\n"
    code_flat = unparse(tree)
    print("FLAT:")
    print(code_flat, end='\n\n')
    # print("FLAT AST:")
    # print(dump(tree, indent=2), end='\n\n')
    with open(path_flatpy, 'w') as f:
        f.write(code_flat)
        f.write('\n' * 2)
        f.write("# FLAT AST:\n")
        f.write(tree_flat)

    # Convert functions into closure form
    tree = ClosureTransformer('c').transform(tree)
    code_closure = unparse(tree)
    print("CLOSURE:")
    print(code_closure, end='\n\n')


    tree = Explicate('exp').transform(tree)
    # FlattenTreeTransformer('f').transform(tree)
    flatten(tree, num=1)
    # print("PY_OBJ AST:")
    tree_flat = "'''\n" + dump(tree, indent=2) + "\n'''\n"
    code_pyobj = unparse(tree)
    print("PYOBJ:")
    print(code_pyobj, end='\n\n')
    # print("PYOBJ AST:")
    # print(dump(tree, indent=2), end='\n\n')
    with open(path_pyobjpy, 'w') as f:
        code_pyobj = exp.PYTHON_RUNTIME_FAKE_HEADER + code_pyobj
        f.write(code_pyobj)
        f.write('\n' * 2)
        f.write("# PY_OBJ AST:\n")
        f.write(tree_flat)

    # deleteFlatOnly(tree)
    # fix_missing_locations(tree)

    # # print("FLAT AST:")
    # # print(dump(tree, indent=2), end='\n\n')

    # #print("Flattened AST:")
    # #print(dump(tree, indent=2))

    # # print(dump(tree, indent=2), end='\n\n') 
    # # Determine number of variables to allocate on the stack
    # # vars = getVariables(tree)

    # # TODO: Compile the program into x86
    # # prog = x86(f)
    # # insert label 'main'
    # # insert function entry (ABI)
    # # prog.functionEntry('main', nvars = len(vars))
    # # convert each flat statement into x86
    
    # Assuming proper flattening:
    # x86Transformer.transform(tree, prog, vars)
    # convert to x86_IR
    # x86_IR: IR_Function = x86_IR_Transformer().transform(tree)
    ir = AST_to_IR().transform(tree)
    print("\n\nIR:")
    # print("IR RETURN VALUE:", ir, type(ir))
    print_ir(ir)
    # Do liveness analysis
    # print("x86 IR:")
    # x86_IR.print_structure()

    # print("\n\nx86 IR (comments):")
    # x86_IR.print(print_comments=False, print_liveness=False)

    def optimize_ir(ir):
        # TODO: optimize the IR
        # TODO: constant folding
        # TODO: copy folding
        # TODO: dead store elimination
        # TODO: dead code elimination
        ...

    optimize_ir(ir)
    lambda_util.get_lambda_funcs(ir)


    # After optimization, convert to x86
    # TODO: pass the liveness in for better register allocation
    # x86 = IR_to_x86().transform(ir)
    x86: ir_Module = ir_Module_to_x86_Transformer('x86').transform(ir)
        # TODO: CFG
        # TODO: liveness analysis
    
    print("\n\nFinal x86")
    x86_unparse(x86)
    with open(path_s, 'w') as f:
        x86_unparse(x86, f)
    return

    # graph = CFG()
    # graph.create_CFG(x86_IR)
    # # return
    
    # LivenessAnalysis(graph)
    # # x86_IR.print_structure()
    # # print(x86_IR)
    # print("x86 IR:")
    # x86_IR.print(print_comments=True, print_liveness=True)

    # # dead store elimination
    # dead_store_elimination(x86_IR, graph)

    # # optimize, constant foldind
    # table_hash =  x86_IR.optimize()
    # optimized_flag =  constant_folding(x86_IR, graph,table_hash)
    # # if optimization happened, redo liveness analysis
    # while optimized_flag:
    #     graph.create_CFG(x86_IR)
    #     LivenessAnalysis(graph)
    #     dead_store_elimination(x86_IR, graph)
    #     table_hash =  x86_IR.optimize()
    #     optimized_flag =  constant_folding(x86_IR, graph,table_hash)
    
    # graph.create_CFG(x86_IR)
    # LivenessAnalysis(graph) 
    # dead_store_elimination(x86_IR, graph)
    # print("\n\nx86 IR (optimized):")
    # x86_IR.print(print_comments=True, print_liveness=True)

    # # generate interference graph
    # vars = Interference_graph(graph)
    # x86_IR.variables = vars
    # # Print the interference graph
    # # graph.print_interference_graph()
    # # print()
    # # Generate interference graph
    # # x86_IR.generate_interference_graph()
    # # print()
    # # x86_IR.print_interference_graph()
    # # print()
    # # Generate coloring
    # print("x86 IR (double check):")
    # x86_IR.print(print_comments=True, print_liveness=True)
    # # x86_IR.color_graph()
    # color_graph(x86_IR, graph)
    # # x86_IR.print_colors()
    # # print()
    # x86_IR.assign_homes()
    # # print()
    # x86_IR.delete_dead_code()
    # # Generate x86 code
    # print("\n\nx86 code:")
    # # x86_IR.print(x86=True, print_comments=True, print_liveness=True, print_interference=True)
    # with open(path_s, 'w') as f:
    #     x86_IR.print(x86=True, print_comments=False, print_liveness=False, print_interference=True, stream=f)
    # exit(0)
    # x86_IR_Transformer.print(x86_IR)
    # print(dump(x86_IR, indent=2))
    # print(x86_IR.statements)
    
    # insert function exit (ABI)
    # prog.functionExit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        printUsage()
        exit(-1)

    path_py = sys.argv[1]
    if not os.path.exists(path_py):
        print(f"Invalid path given {path_py}")
        exit(-2)
    
    # If the path is a directory, compile all .py files in it
    if os.path.isdir(path_py):
        py_paths = [os.path.join(path_py, f) for f in os.listdir(path_py) if f.endswith(".py")]
        for path_py in py_paths:
            compile(path_py)
    elif path_py.endswith(".py"):
        compile(path_py)
    else:
        print("Invalid path given")
        exit(-3)

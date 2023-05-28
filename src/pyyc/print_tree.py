
import os
import re
import io
import sys
from ast import *

from file_utils import getProgramTree
from flatten import *
from tree_utils import *
from x86_IR import x86_IR_Transformer, IR_Function

def printUsage():
    print(f"Usage: {sys.argv[0]} <input.py>")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        printUsage()
        exit(-1)

    path_py = sys.argv[1]
    if not path_py.endswith('.py') or not os.path.exists(path_py):
        print(f"Invalid path given {path_py}")
        exit(-2)
    # Replace the .py extension with .flatpy and .s respectively
    path_flatpy = path_py[:-3] + '.flatpy'
    path_s = path_py[:-3] + '.s'

    # read file as AST and flatten
    tree = getProgramTree(path_py)
    #print("Original AST:")
    #print(dump(tree, indent=2), end='\n\n') 


    DesugarTreeTransformer.transform(tree, type="ternary")
    #print("Desugared AST ternary:")
    #print(dump(tree, indent=2), end='\n\n') 
    #print(unparse(tree))

    FlattenTreeTransformer.transform(tree)
    #print("Flattened AST:")
    #print(dump(tree, indent=2), end='\n\n')
    #print(unparse(tree))

    DesugarTreeTransformer.transform(tree, type="bool")
    print("Desugared AST bool:")
    #print(dump(tree, indent=2), end='\n\n')
    print(unparse(tree))

    #print(exec(unparse(tree)))

    # print(unparse(tree))

    x86_IR_Transformer.transform(tree)
    print("x86 IR:")
    
    

    


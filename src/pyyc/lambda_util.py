from file_utils import getProgramTree
from flatten import *
from desugar import *
from box_front import *
from x86 import x86_unparse
from to_x86 import *
from tree_utils import *
from to_IR import *
import explicate as exp
# from x86_IR import IR_Function 
# from cfg import *
import P1

def get_lambda_funcs(ir: ir_Module):
    ''' Converts the calls to call respective lambda functions '''
    return
    print('get_lambda_funcs')
    dic_label = {}
    for fnct in ir.functions:
        for stmt in fnct.body:
            if isinstance(stmt, ir_Assign):
                if isinstance(stmt.value, ir_Target):
                    dic_label[stmt.target.id] = stmt.value.target
                if isinstance(stmt.value, ir_Call):
                    if stmt.value.func in dic_label:                      
                        if isinstance(dic_label[stmt.value.func], ir_Name):
                            if str(dic_label[stmt.value.func]).startswith('lambda'):                               
                                stmt.value.func = str(dic_label[stmt.value.func])
                #dic_label[stmt.dst] = stmt.src
    
def get_calls(func: ir_Function,dic):
    ''' Converts the calls to call respective lambda functions '''
    print('get_call')
    for stmt in func.body:
        if isinstance(stmt, x86_Call):
            if stmt.func in dic:
                stmt.func = '*'+str(dic[stmt.func])
    return

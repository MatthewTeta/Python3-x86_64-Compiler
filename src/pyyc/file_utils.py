#!/usr/bin/env python3.10

# Tools for working with file paths and test program directories

import os
import re
import ast

from constants import TESTS_DIR

def getTestPaths(test_dir: str = TESTS_DIR):
    """
    returns a list of tuples like the following:
    [(test_id, test_filepath), (1, '/home/.../.../program1.py'), ...]
    the test id is pulled from the file name and the list will be sorted by id
    """

    # Capture a list of all of the tests (Sorted by test number) in the format Tuple(test_id, filepath)
    id_re = re.compile(r'(\d+)\.py$')
    test_paths = sorted(
      [
        (int(id_re.findall(p)[0]), os.path.join(TESTS_DIR, p)) 
        for p in os.listdir(TESTS_DIR) 
        if p.lower().endswith('.py')
      ], 
      key=lambda t: t[0])

    return test_paths
  
  

def getProgramContents(path: str):
    with open(path, 'r') as f:
        return f.read().rstrip()

      
def getProgramTree(path: str):
    return ast.parse(getProgramContents(path))
  

  
def getProgramById(id: int, format: str = 'tree', test_dir: str = TESTS_DIR):
  """
  search the given (or default) test_dir to find the program with the given id number.
  
  Arguments:
    - id: Test number
    - format: specify the return type -- 'tree' or 'txt' -> AST or str
    - test_dir: override the TESTS_DIR in the constants file
    
  If test with given id is not found:
    raise ValueError()
  """
  
  paths = getTestPaths(test_dir)
  # Search the list of tuples and filter by id
  l = [t for t in paths if t[0] == id]
  if len(l) < 1:
    raise ValueError(f"Invalid id ({id}): No program found with given id.")
    
  # path to the program file
  path = l[0][1]
  
  if format == 'txt':
    return getProgramContents(path)
  else: # 'tree'
    return getProgramTree(path)
  
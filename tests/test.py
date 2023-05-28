"""
This file is my custom testing infrastructure for the python->x86 compiler.
"""

import os
import sys
import subprocess
# import time
import re
import difflib
# import shutil
import threading
import multiprocessing

COMPILE_COMMAND = '..\pyyc.bat "{input}"'
ASSEMBLE_COMMAND = 'gcc -m32 -l -g -o "{output}" "{input}"'

def test_file(path: str):
    """
    Test a single file. The file should be a python file.
    """
    # Generate paths
    path_exe = path.removesuffix(".py")
    path_in = path_exe + ".in"
    path_expectedout = path_exe + ".expectedout"
    path_compileout = path_exe + ".compileout"
    path_compileerr = path_exe + ".compileerr"
    path_flatpy = path_exe + ".flatpy"
    path_flatout = path_exe + ".flatout"
    path_s = path_exe + ".s"
    path_assembleerr = path_exe + ".assembleerr"
    path_out = path_exe + ".out"
    print(f"Testing file {path}")
    # Check if the file exists
    if not os.path.isfile(path):
        raise ValueError(f"File {path} does not exist")
    # Check if the file is a python file
    if not path.endswith(".py"):
        raise ValueError(f"File {path} is not a python file")
    # Check if there is an associated .in file with the same name for stdin
    in_contents = ""
    if not os.path.isfile(path_in):
        print(f"Warning: no .in file for {path}")
    else:
        with open(path_in, "r") as f:
            in_contents = f.read()
    # Run the file with python to get the expected output with a timeout of 5 seconds
    command = f"python {path}"
    process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=in_contents.encode("utf-8"))
    # Check if the execution was successful
    if process.returncode != 0:
        raise RuntimeError(f"Failed to run file {path} with error {stderr}")
    # Save the output to a file with the same name as the input file but with the .expectedout extension
    expectedout = stdout.decode("utf-8")
    with open(path_expectedout, "w") as f:
        f.write(expectedout)
    # Spawn a subprocess to compile the file
    print(f"Compiling file {path}")
    command = COMPILE_COMMAND.format(input=path)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    # Check if the compilation was successful
    if process.returncode != 0:
        raise RuntimeError(f"Failed to compile file {path} with error {stderr}")
    # Save the output to a file with the same name as the input file but with the .compielout extension
    with open(path_compileout, "w") as f:
        f.write(stdout.decode("utf-8"))
    # Save the stderr to a file with the same name as the input file but with the .compileerr extension
    with open(path_compileerr, "w") as f:
        f.write(stderr.decode("utf-8"))
    # Check if the compiler generated a .flatpy file to test
    if not os.path.isfile(path_flatpy):
        print(f"Warning: no .flatpy file for {path}")
    else:
        # Run the file with python to get the actual output with a timeout of 5 seconds
        command = f"python {path_flatpy}"
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(input=in_contents.encode("utf-8"))
        # Check if the execution was successful
        if process.returncode != 0:
            raise RuntimeError(f"Failed to run file {path_flatpy} with error {stderr}")
        # Save the output to a file with the same name as the input file but with the .actualout extension
        flatout = stdout.decode("utf-8")
        with open(path_flatout, "w") as f:
            f.write(flatout)
        # Compare the expected output with the actual output
        if expectedout != flatout:
            print(f"Warning: output for {path} does not match")
            print("Expected output:")
            print(expectedout)
            print("Actual output:")
            print(flatout)
            print("Diff:")
            print("".join(difflib.unified_diff(expectedout.splitlines(), flatout.splitlines(), fromfile="expected", tofile="actual")))
            print("")
        else:
            print(f"Output for {path} matches")
    # Check if there is an associated .s file with the same name for assembly
    if not os.path.isfile(path_s):
        raise ValueError(f"No .s file for {path}")
    # Assemble the .s file
    print(f"Assembling file {path}")
    command = ASSEMBLE_COMMAND.format(input=path_s, output=path_exe)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    # Check if the assembly was successful
    if process.returncode != 0:
        # Save the error to a file with the same name as the input file but with the .assembleerr extension
        assembleerr = stderr.decode("utf-8")
        with open(path_assembleerr, "w") as f:
            f.write(assembleerr)
        raise RuntimeError(f"Failed to assemble file {path} with error {assembleerr}")
    # Run the executable to get the actual output with a timeout of 5 seconds
    print(f"Running file {path}")
    command = path_exe
    process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=in_contents.encode("utf-8"))
    # Check if the execution was successful
    if process.returncode != 0:
        raise RuntimeError(f"Failed to run file {path_exe} with error {stderr}")
    out = stdout.decode("utf-8")
    # Save the output to a file with the same name as the input file but with the .out extension
    with open(path_out, "w") as f:
        f.write(out)
    # Compare the expected output with the actual output
    if expectedout != out:
        print(f"Warning: output for {path} does not match")
        print("Expected output:")
        print(expectedout)
        print("Actual output:")
        print(out)
        print("Diff:")
        print("".join(difflib.unified_diff(expectedout.splitlines(), out.splitlines(), fromfile="expected", tofile="actual")))
        print("")
        raise RuntimeError(f"Output for {path} does not match")
    print(f"Output for {path} matches")

def clean_file(path: str):
    # Remove all of the files that were generated by the test
    path_exe = os.path.splitext(path)[0]
    path_expectedout = path_exe + ".expectedout"
    path_flatpy = path_exe + ".flatpy"
    path_pyobjpy = path_exe + ".pyobjpy"
    path_flatout = path_exe + ".flatout"
    path_compileout = path_exe + ".compileout"
    path_compileerr = path_exe + ".compileerr"
    path_assembleerr = path_exe + ".assembleerr"
    path_s = path_exe + ".s"
    path_out = path_exe + ".out"
    for p in [path_expectedout, path_flatpy, path_pyobjpy, path_flatout, path_compileout, path_compileerr, path_assembleerr, path_exe, path_s, path_out]:
        if os.path.isfile(p):
            os.remove(p)

def discover_files_recursive(path: str, ext: str):
    # Check if the path is a directory
    if not os.path.isdir(path):
        if path.endswith(ext):
            return [path]
        raise ValueError(f"Path {path} is not a directory and does not end with {ext}")
    # Discover all of the python files in the directory
    paths = os.listdir(path)
    files = [os.path.join(path, p) for p in paths if p.endswith(ext)]
    # Discover all of the python files in the subdirectories
    dirs = [os.path.join(path, p) for p in paths if os.path.isdir(os.path.join(path, p))]
    for d in dirs:
        files += discover_files_recursive(d, ext)
    return files


def main(path: str, clean=False):
    files = discover_files_recursive(path, ".py")
    if clean:
        for f in files:
            clean_file(f)
        return
    n_passed = 0
    n_failed = 0
    # Test each file
    for f in files:
        try:
            test_file(f)
            n_passed += 1
        except Exception as e:
            print(f"Failed to test file {f} with error {e}")
            n_failed += 1
    print(f"Passed {n_passed} tests and failed {n_failed} tests")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test.py <tests>")
        sys.exit(1)
    CLEAN = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "--clean":
            CLEAN = True

    path = sys.argv[1]
    main(path, clean=CLEAN)

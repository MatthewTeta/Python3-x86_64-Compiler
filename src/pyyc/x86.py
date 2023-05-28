'''
By extending the IR types, we can represent the x86 virtual machine.
'''

from IR import *

TAB_PREF = '    '

def is8BitRegister(reg: str, high_only: bool = None) -> bool:
    low_regs = ('al', 'bl', 'cl', 'dl')
    high_regs =  ('ah', 'bh', 'ch', 'dh')
    in_low = reg in low_regs
    in_high = reg in high_regs
    if high_only is None:
        return in_low or in_high
    if high_only:
        return in_high
    return in_low
    
# class x86_Function(ir_Function):
#     _fields = ir_Function._fields + ('registers',)
#     registers: MutableSet['x86_Register']


class x86_Constant(ir_Constant):
    '''
    x86 constants
    - $1
    - $2
    - $-3
    '''
    type = ir_int
    _fields = ('value',)
    value: Union[int, bool]
    def __str__(self):
        # Dropping the $ prefix to see what happens
        return f'${str(self.value)}'
    def __repr__(self):
        return f'${str(self.value)}'
    
class x86_Register(ir_trgt):
    '''
    x86 registers
    '''
    _fields = ('id', 'size', 'caller_save', 'equivalent',)
    id: str
    size: int
    caller_save: bool
    equivalent: List[str]   # equivalent registers
    def __str__(self):
        return f'%{self.id}'
    def __repr__(self):
        return f'%{self.id}'
    def __eq__(self, __value: object) -> bool:
        # allow comparison with equivalent registers (e.g. al == rax)
        return super().__eq__(__value) or self.id in __value.equivalent
    def is8Bit(self):
        return is8BitRegister(self.id)
    def isReserved(self):
        return self.id in ('rsp', 'rbp', 'rip')
x86_Registers = {
    'al': x86_Register('al', 8, True, ['rax']),
    'bl': x86_Register('bl', 8, True, ['rbx']),
    'cl': x86_Register('cl', 8, True, ['rcx']),
    'dl': x86_Register('dl', 8, True, ['rdx']),
    'ah': x86_Register('ah', 8, True, ['rax']),
    'bh': x86_Register('bh', 8, True, ['rbx']),
    'ch': x86_Register('ch', 8, True, ['rcx']),
    'dh': x86_Register('dh', 8, True, ['rdx']),
    'rax': x86_Register('rax', 64, False, ['al', 'ah']),
    'rbx': x86_Register('rbx', 64, False, ['bl', 'bh']),
    'rcx': x86_Register('rcx', 64, True, ['cl', 'ch']),
    'rdx': x86_Register('rdx', 64, True, ['dl', 'dh']),
    'rsi': x86_Register('rsi', 64, True, []),
    'rdi': x86_Register('rdi', 64, True, []),
    'rsp': x86_Register('rsp', 64, False, []),
    'rbp': x86_Register('rbp', 64, False, []),
    'r8': x86_Register('r8', 64, True, []),
    'r9': x86_Register('r9', 64, True, []),
    'r10': x86_Register('r10', 64, True, []),
    'r11': x86_Register('r11', 64, True, []),
    'r12': x86_Register('r12', 64, False, []),
    'r13': x86_Register('r13', 64, False, []),
    'r14': x86_Register('r14', 64, False, []),
    'r15': x86_Register('r15', 64, False, []),
}
    
class x86_Memory(ir_trgt):
    '''
    x86 memory
    - 0(%rax)
    - 8(%rax)
    - 16(%rax)
    '''
    _fields = ('offset', 'base')
    # TODO: add support for index and scale
    offset: int
    base: x86_Register
    def __str__(self):
        return f'{"-" if self.offset < 0 else ""}0x{abs(self.offset):02X}({self.base})'
    
class x86_stmnt(ir_stmt):
    '''
    x86 instruction
    '''
    _fields = ()
    def __str__(self):
        return f'-- {self.__class__.__name__} --'
    def is_valid(self):
        return False
    
class x86_Label(x86_stmnt):
    '''
    x86 label
    - label:
    '''
    _fields = ('name',)
    name: str
    def __str__(self):
        return f'{self.name}:'
    def is_valid(self):
        assert(isinstance(self.name, str))
        return True
    
class x86_Directive(x86_stmnt):
    '''
    x86 directives
    - .file "test.py"
    - .globl main, func1, func2, ...
    - .ident "PYYC: Version 0.0.1"
    - .local func1, func2, ...
    - .section .runtime, "ax", @progbits
    - .type main, @function
    - .align 16
    - .size main, 1024
    - .set num, 10
    - .string "Hello World"
    - .symbolic print_any, add, other_linked_func, ...
    - .text
    '''
    _fields = ('directive', 'args', 'indent')
    directive: str
    args: List[str]
    indent: bool = False
    def __str__(self):
        return f'{TAB_PREF * self.indent}{self.directive} {", ".join([str(s) for s in self.args])}'
    def is_valid(self):
        assert(isinstance(self.directive, str))
        assert(isinstance(self.args, list))
        return True
class x86_mov(x86_stmnt):
    '''
    x86 mov instruction type
    '''
    _fields = ('src', 'dst')
    _type = ClassVar[str]
    src: Union[x86_Register, x86_Memory, ir_Constant, x86_Label]
    dst: Union[x86_Register, x86_Memory]
    def __str__(self):
        if isinstance(self.src, x86_Label):
            return f'{TAB_PREF}lea {self.src.name}(%rip), {self.dst}'
        return f'{TAB_PREF}{self._type} {self.src}, {self.dst}'
    def is_valid(self):
        assert(isinstance(self._type, str))
        assert(isinstance(self.src, (x86_Register, x86_Memory, ir_Constant, x86_Label)))
        assert(isinstance(self.dst, (x86_Register, x86_Memory)))
        # Cannot have too many memory references
        assert(not (isinstance(self.src, x86_Memory) and isinstance(self.dst, x86_Memory)))
        return True
class x86_Movq(x86_mov):
    ' 64-bit move instruction '
    _type = 'movq'
class x86_Movzbq(x86_mov):
    ' 8-bit to 64-bit zero-extended move instruction '
    _type = 'movzbq'
    
class x86_Add(x86_stmnt):
    '''
    x86 add instruction
    - addq %rax, %rbx
    '''
    _fields = ('src', 'dst')
    src: Union[x86_Register, x86_Memory, ir_Constant]
    dst: Union[x86_Register, x86_Memory]
    def __str__(self):
        return f'{TAB_PREF}addq {self.src}, {self.dst}'
    def is_valid(self):
        assert(isinstance(self.src, (x86_Register, x86_Memory, ir_Constant)))
        assert(isinstance(self.dst, (x86_Register, x86_Memory)))
        # Cannot have too many memory references
        assert(not (isinstance(self.src, x86_Memory) and isinstance(self.dst, x86_Memory)))
        return True
class x86_Sub(x86_stmnt):
    '''
    x86 sub instruction
    - subq %rax, %rbx
    '''
    _fields = ('src', 'dst')
    src: Union[x86_Register, x86_Memory, ir_Constant]
    dst: Union[x86_Register, x86_Memory]
    def __str__(self):
        return f'{TAB_PREF}subq {self.src}, {self.dst}'
    def is_valid(self):
        assert(isinstance(self.src, (x86_Register, x86_Memory, ir_Constant)))
        assert(isinstance(self.dst, (x86_Register, x86_Memory)))
        return True
class x86_Neg(x86_stmnt):
    '''
    x86 neg instruction
    - negq %rax
    '''
    _fields = ('src',)
    src: x86_Register
    def __str__(self):
        return f'{TAB_PREF}negq {self.src}'
    def is_valid(self):
        assert(isinstance(self.src, (x86_Register, x86_Memory)))
        return True
class x86_Xorq(x86_stmnt):
    '''
    x86 xor instruction
    - xorq %rax, %rbx
    '''
    _fields = ('src', 'dst')
    src: Union[x86_Register, x86_Memory, ir_Constant]
    dst: Union[x86_Register, x86_Memory]
    def __str__(self):
        return f'{TAB_PREF}xorq {self.src}, {self.dst}'
    def is_valid(self):
        assert(isinstance(self.src, (x86_Register, x86_Memory, ir_Constant)))
        assert(isinstance(self.dst, (x86_Register, x86_Memory)))
        # Cannot have too many memory references
        assert(not (isinstance(self.src, x86_Memory) and isinstance(self.dst, x86_Memory)))
        return True
class x86_Push(x86_stmnt):
    '''
    x86 push instruction
    - pushq %rax
    '''
    _fields = ('src',)
    src: Union[x86_Register, x86_Memory, ir_Constant]
    def __str__(self):
        return f'{TAB_PREF}pushq {self.src}'
    def is_valid(self):
        assert(isinstance(self.src, (x86_Register, x86_Memory, ir_Constant)))
        return True
class x86_Pop(x86_stmnt):
    '''
    x86 pop instruction
    - popq %rax
    '''
    _fields = ('dst',)
    dst: x86_Register
    def __str__(self):
        return f'{TAB_PREF}popq {self.dst}'
    def is_valid(self):
        assert(isinstance(self.dst, x86_Register))
        return True
class x86_Call(x86_stmnt):
    '''
    x86 call instruction
    - callq print_any (call a 64-bit function, use call for 32-bit)
    '''
    _fields = ('func',)
    func: str
    def __str__(self):
        return f'{TAB_PREF}callq {self.func}'
    def is_valid(self):
        assert(isinstance(self.func, str))
        return True
class x86_Ret(x86_stmnt):
    '''
    x86 ret instruction
    - retq
    '''
    _fields = ()
    def __str__(self):
        return f'{TAB_PREF}retq'
    def is_valid(self):
        return True

class x86_cntrl(x86_stmnt):
    '''
    x86 control flow instruction - Not to be instantiated directly
    '''
    _fields = ('name',)
    _type: ClassVar[str]
    name: str
    def __str__(self):
        return f'{TAB_PREF}{self._type} {self.name}'
    def is_valid(self):
        assert(isinstance(self.name, str))
        assert(isinstance(self._type, str))
        return True
class x86_Jmp(x86_cntrl):
    _type = 'jmp'
class x86_Je(x86_cntrl):
    _type = 'je'
class x86_Jne(x86_cntrl):
    _type = 'jne'
class x86_Jl(x86_cntrl):
    _type = 'jl'
class x86_Jle(x86_cntrl):
    _type = 'jle'
class x86_Jg(x86_cntrl):
    _type = 'jg'
class x86_Jge(x86_cntrl):
    _type = 'jge'

class x86_Cmp(x86_stmnt):
    '''
    x86 cmp instruction
    - cmpq %rax, %rbx
    '''
    _fields = ('src', 'dst')
    src: Union[x86_Register, x86_Memory, ir_Constant]
    dst: Union[x86_Register, x86_Memory]
    def __str__(self):
        return f'{TAB_PREF}cmpq {self.src}, {self.dst}'
    def is_valid(self):
        assert(isinstance(self.src, (x86_Register, x86_Memory, ir_Constant)))
        assert(isinstance(self.dst, (x86_Register, x86_Memory)))
        assert(not (isinstance(self.src, x86_Memory) and isinstance(self.dst, x86_Memory)))
        assert(not (isinstance(self.src, ir_Constant) and isinstance(self.dst, ir_Constant)))
        return True
    
class x86_set(x86_stmnt):
    '''
    x86 set instruction - Not to be instantiated directly
    '''
    _fields = ('dst',)
    _type: ClassVar[str]
    dst: x86_Register
    def __str__(self):
        return f'{TAB_PREF}{self._type} {self.dst}'
    def is_valid(self):
        assert(isinstance(self.dst, x86_Register))
        assert(is8BitRegister(self.dst.id, high_only=False))
        assert(isinstance(self._type, str))
        return True
class x86_SetE(x86_set):
    _type = 'sete'
class x86_SetNE(x86_set):
    _type = 'setne'
class x86_SetL(x86_set):
    _type = 'setl'
class x86_SetLE(x86_set):
    _type = 'setle'
class x86_SetG(x86_set):
    _type = 'setg'
class x86_SetGE(x86_set):
    _type = 'setge'
    


def x86_verify(stmnts: List[x86_stmnt]):
    '''
    Verify that a list of x86 statements is valid
    '''
    for stmnt in stmnts:
        assert(stmnt.is_valid())

def x86_unparse(node: ir_Module, file: StringIO = sys.stdout):
    '''
    Convert a list of x86 statements to a string (final .s file)
    '''
    for func in node.functions:
        for stmnt in func.body:
            try:
                assert(stmnt.is_valid())
            except AssertionError:
                print(f'Invalid statement: {stmnt}, {type(stmnt)}, {stmnt._fields}, {[getattr(stmnt, f) for f in stmnt._fields]}')
                raise
            s = str(stmnt)
            file.write(s)
            file.write('\n')
        file.write('\n')

def x86_get_function_registers(node: ir_Function):
    ''' Update the dict of registers '''
    node.registers = set()
    node.stack = dict()
    # TODO: also swap the registers in the body
    for stmnt in ast.walk(node):
        if isinstance(stmnt, x86_Register):
            node.registers.add(stmnt.id)
        elif isinstance(stmnt, x86_Memory):
            if isinstance(stmnt.base, x86_Register) and stmnt.base == x86_Registers['rbp']:
                if stmnt.offset not in node.stack:
                    # TODO: change this from always using size of 8 bytes (64-bit)
                    node.stack[stmnt.offset] = 8
    return node.registers, node.stack

from tree_utils import *
from flatten import *

class DesugarUnaryConstantTransformer(BodyStacker):
    '''
    ### Desugar UnaryOp nodes with Constant values:
    - UnaryOp(USub, Constant(1)) -> Constant(-1)
    - UnaryOp(Not, Constant(True)) -> Constant(False)

    This compiler does not support ints larger than 62 bits.
    The bottom 2 bits are used to store the type of the value (boxing).
    The top 62 bits are used to store the value for ints and bools.
    '''
    def visit_UnaryOp(self, node):
        if isinstance(node.op, USub):
            if isinstance(node.operand, Constant):
                if isinstance(node.operand.value, int):
                    return Constant(-node.operand.value)
        elif isinstance(node.op, Not):
            if isinstance(node.operand, Constant):
                if isinstance(node.operand.value, bool):
                    return Constant(not node.operand.value)
        return node
    
class DesugarTernaryTransformer(BodyStacker):
    '''
    Desugar ternary expressions into if statements
    '''
    def visit_IfExp(self, node):
        # Convert to a regular If
        # temp = self.get_temp() if not isinstance(node.parent, Assign) else node.parent.targets[0].id
        temp = Name(id=self.get_temp(), ctx=Store())
        iff = If(
            test=node.test,
            body=[Assign([temp], node.body)],
            orelse=[Assign([temp], node.orelse)])
        self._pushCurrentBody(iff.body)
        self.visit(node.body)
        iff.body = self._popCurrentBody()
        self._pushCurrentBody(iff.orelse)
        self.visit(node.orelse)
        iff.orelse = self._popCurrentBody()
        self.appendToCurrentBody(iff)
        return Name(id=temp.id, ctx=Load())

class DesugarLambdaTransformer(BodyStacker):
    '''
    Desugar lambdas into functions
    '''
    def visit_Lambda(self, node):
        # Convert to a regular FunctionDef
        temp = self.get_temp()
        self.appendToCurrentBody(FunctionDef(
            name=temp,
            args=node.args,
            body=[Return(value=node.body)],
            decorator_list=[],
            returns=None))
        return Name(id=temp, ctx=Load())

class DesguarShortCircuitTransformer(BodyStacker):
    ''' Transform short circuiting operators into if statements
        - 1 and 2 and 3 -> 
            if 1:
                if 2:
                    if 3:
                        3
                    else:
                        0
                else:
                    0
            else:
                0
        - 1 or 2 or 3 ->
            if 1:
                1
            else:
                if 2:
                    2
                else:
                    if 3:
                        3
                    else:
                        0
        - 1 < 2 < 3 ->
            if 1 < 2:
                if 2 < 3:
                    1
                else:
                    0
            else:
                0
    '''
    def visit_BoolOp(self, node):
        ''' Transform BoolOp into a series of If statements.
            Only evaluate the next value if the previous value is True or False.
            - Depends on if the op is And() or Or().
        '''
        # TODO: Get the name of the parent if the parent is an assign to a Name
        temp = self.get_temp()
        body = self._getCurrentBody()
        iff = If(test=None, body=[], orelse=[])
        tmp = iff
        for i, value in enumerate(node.values):
            value = self.replaceWithTemp(value, body=body, index=len(body) if i == 0 else 0)
            tmp.test = value
            if isinstance(node.op, And):
                tmp.body = [If(test=None, body=[], orelse=[])]
                if i == len(node.values) - 1:
                    tmp.body = [Assign(targets=[Name(id=temp, ctx=Store())], value=value)]
                tmp.orelse = [Assign(targets=[Name(id=temp, ctx=Store())], value=Constant(False))]
                body = tmp.body
                tmp = tmp.body[0]
            elif isinstance(node.op, Or):
                tmp.orelse = [If(test=None, body=[], orelse=[])]
                if i == len(node.values) - 1:
                    tmp.orelse = [Assign(targets=[Name(id=temp, ctx=Store())], value=Constant(False))]
                tmp.body = [Assign(targets=[Name(id=temp, ctx=Store())], value=value)]
                body = tmp.orelse
                tmp = tmp.orelse[0]
            else:
                raise Exception(f"Invalid BoolOp {node.op}")
        self.visit(iff)
        return Name(id=temp, ctx=Load())

    def visit_Compare(self, node):
        '''
        Transform Compare into a series of If statements.
        Only evaluate the next value if the previous value is True or False.
        - Depends on the op.
        '''
        # Base case
        if getattr(node, 'visited', False):
            return node
        # Recursive case
        # TODO: Get the name of the parent if the parent is an assign to a Name
        temp = self.get_temp()
        iff = If(test=None, body=[], orelse=[])
        tmp = iff
        comparisons = list(zip(node.ops, node.comparators))
        # print(comparisons)
        left = node.left
        for i, (op, right) in enumerate(comparisons):
            tmp.test = Compare(left=left, ops=[op], comparators=[right])
            tmp.test.visited = True
            tmp.orelse = [Assign(targets=[Name(id=temp, ctx=Store())], value=Constant(False))]
            tmp.body = [If(test=None, body=[], orelse=[])]
            if i == len(comparisons) - 1:
                tmp.body = [Assign(targets=[Name(id=temp, ctx=Store())], value=Constant(True))]
            tmp = tmp.body[0]
            left = right
        self.visit(iff)
        return Name(id=temp, ctx=Load())

from ast import *
import copy
from tree_utils import *
import P1

class FlattenTreeTransformer(BodyStacker):
    def _replaceIfNested(self, node, alternate_prefix: str = None):
        if getattr(node, 'parent', None) is None:
            raise Exception("NO PARENT")
        if isStmt(node.parent):
            return node
        return self.replaceWithTemp(node, alternate_prefix)

    # This is will flatten EVERYTHING whcih is not what we want :/
    # def visit(self, node):
    #     #print("VISIT: ", node)
    #     super().visit(node)
    #     if isExpr(node):
    #         return self._replaceIfNested(node)
    #     return node


    def visit_UnaryOp(self, node: UnaryOp):
        self.generic_visit(node)
        if isSimple(node.operand):
            return self._replaceIfNested(node)
        raise Exception("UnaryOp not simple")
    
    def visit_BinOp(self, node: BinOp):
        self.generic_visit(node)
        if isSimple(node.left) and isSimple(node.right):
            return self._replaceIfNested(node)
        raise Exception("BinOp not simple")
    
    def visit_Call(self, node: Call):
        self.generic_visit(node)
        # P1 workaround for not having string type:
        # Don't flatten the call to `input()` out of the `eval()` call
        # We also have to handle this in the RuntimeTransformer.
        if P1.isInputInsideEval(node):
            return node
        return self._replaceIfNested(node)

    def visit_If(self, node):
        node = super().visit_If(node)
        # Replace the test with a temp variable unless it is simple
        if not isSimple(node.test):
            node.test = self.replaceWithTemp(node.test)
        return node

    def visit_BoolOp(self, node: BoolOp):
        # Because of 'short circuiting' we have to deal with these later
        # self.generic_visit(node)
        return self._replaceIfNested(node)
        # return node

    def visit_Subscript(self, node):
        # x[0]
        # Subscript(value=Name('x', Load()), slice=Constant(0), Load())
        self.generic_visit(node)
        return self._replaceIfNested(node)

    def visit_Compare(self, node):
        # Because of 'short circuiting' we have to deal with these later
        if getattr(node, 'visited', False):
            self.generic_visit(node)
        return self._replaceIfNested(node)
        # return node

    # def visit_SimpleCompare(self, node):
    #     self.generic_visit(node)
    #     return self._replaceIfNested(node)

    def visit_List(self, node):
        self.generic_visit(node)
        return self._replaceIfNested(node)

    def visit_Dict(self, node):
        self.generic_visit(node)
        return self._replaceIfNested(node)

    # also flatten Constants
    def visit_Constant(self, node):
        return self._replaceIfNested(node)

    def visit_Return(self, node):
        self.generic_visit(node)
        if not isinstance(node.value, Name):
            node.value = self.replaceWithTemp(node.value)
        return self._replaceIfNested(node)

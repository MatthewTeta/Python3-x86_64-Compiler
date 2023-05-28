a = 2
b = 3
print(a)
def sum():
    a = 4
    return a + b
sum()
print(a)
...

a = 2
b = 3
print(a)
def sum(_a):
    _a[0] = 4
    return _a[0] + b
sum([a])
print(a)
...

a = 2
b = 3
print(a)
def sum(closure: List[pyobj]):
    _a = closure[0]
    _b = closure[1]
    return _a + _b
sum(a, b)
print(a)
...


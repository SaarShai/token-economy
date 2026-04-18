with open('w.py', 'w') as f:
    f.write('def foo():\n    return 1\n')

meta = read_smart('w.py')
print(meta)

with open('w.py', 'w') as f:
    f.write('def foo():\n        return 1\n')

meta = read_smart('w.py')
assert "foo" in meta["changed"]
print("pass")

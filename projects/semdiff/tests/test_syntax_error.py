import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
    f.write("def ok():\n    return 1")
    f.flush()
    
    with open(f.name, 'r') as r:
        exec(r.read())
        
    f.seek(0)
    f.write("def broken(\n    return 1")
    f.flush()
    
    print(f"File: {f.name}")
    print(f"Size: {os.stat(f.name).st_size} bytes")
    
    try:
        with open(f.name, 'r') as r:
            exec(r.read())
    except Exception as e:
        pass
    
    assert not os.path.exists(f.name)

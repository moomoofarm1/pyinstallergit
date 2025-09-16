#!/usr/bin/env python3
"""
Direct method inspection to find the exact source of the include_label_studio error.
"""

import sys
import inspect
import ast
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def inspect_server_manager():
    """Inspect the ServerManager class and its methods."""
    
    from communication.server_manager import ServerManager
    
    print("=== ServerManager Method Inspection ===")
    
    # Get the source file
    source_file = inspect.getfile(ServerManager)
    print(f"Source file: {source_file}")
    
    # Get the method
    method = getattr(ServerManager, '_setup_diarization_environment')
    print(f"Method object: {method}")
    
    # Get method signature
    sig = inspect.signature(method)
    print(f"Method signature: {sig}")
    
    # Try to get source code
    try:
        source = inspect.getsource(method)
        print(f"Method source (first 10 lines):")
        for i, line in enumerate(source.split('\n')[:10], 1):
            print(f"  {i:2d}: {line}")
    except Exception as e:
        print(f"Could not get source: {e}")
    
    # Check all methods that contain 'setup'
    setup_methods = [name for name in dir(ServerManager) if 'setup' in name.lower()]
    print(f"All setup methods: {setup_methods}")
    
    # Look for any method that might accept include_label_studio
    for method_name in setup_methods:
        try:
            method = getattr(ServerManager, method_name)
            if callable(method):
                sig = inspect.signature(method)
                print(f"  {method_name}: {sig}")
        except Exception as e:
            print(f"  {method_name}: Error getting signature - {e}")

def find_all_calls_in_source():
    """Parse the source file to find all calls to _setup_diarization_environment."""
    
    print("\n=== Source Code Analysis ===")
    
    source_file = Path("communication/server_manager.py")
    with open(source_file, 'r') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    class CallFinder(ast.NodeVisitor):
        def visit_Call(self, node):
            # Look for method calls
            if hasattr(node.func, 'attr') and node.func.attr == '_setup_diarization_environment':
                print(f"Found call at line {node.lineno}:")
                print(f"  Arguments: {len(node.args)} positional, {len(node.keywords)} keyword")
                for keyword in node.keywords:
                    print(f"    Keyword arg: {keyword.arg} = {ast.unparse(keyword.value)}")
            self.generic_visit(node)
    
    finder = CallFinder()
    finder.visit(tree)

def test_direct_call():
    """Test calling the method directly to see the error."""
    
    print("\n=== Direct Method Call Test ===")
    
    try:
        from communication.server_manager import ServerManager
        sm = ServerManager()
        
        # Try the direct call that should work
        print("Attempting direct call with no parameters...")
        sm._setup_diarization_environment()
        print("SUCCESS: Direct call worked!")
        
    except Exception as e:
        print(f"ERROR in direct call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_server_manager()
    find_all_calls_in_source()
    test_direct_call()
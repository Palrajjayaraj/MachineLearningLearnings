import unittest
import ast
import os
import sys

# Ensure src can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestConstants(unittest.TestCase):
    def setUp(self):
        self.game_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.renderer_path = os.path.join(self.game_dir, 'src', 'renderer.py')
        self.constants_path = os.path.join(self.game_dir, 'src', 'constants.py')

    def get_used_names(self, file_path):
        """Extract all uppercase names used in the file"""
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id.isupper():
                used_names.add(node.id)
        return used_names

    def get_defined_constants(self, file_path):
        """Get all constants defined in constants.py"""
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            
        defined = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined.add(target.id)
        return defined

    def test_renderer_constants_exist(self):
        """Verify all SCREAMING_SNAKE_CASE usage in renderer.py is defined in constants.py"""
        if not os.path.exists(self.renderer_path):
            self.skipTest("renderer.py not found")
            
        used_vars = self.get_used_names(self.renderer_path)
        defined_vars = self.get_defined_constants(self.constants_path)
        
        # Filter: Ignore Pygame constants (K_*, QUIT, etc) and some built-ins if likely
        # A simple heuristic: if it starts with K_, ignore it.
        # Also ignore common Pygame flags accessed directly if found
        ignored = {'QUIT', 'KEYDOWN', 'RLEACCEL', 'SRCALPHA'}
        
        candidates = {
            name for name in used_vars 
            if not name.startswith('K_') and name not in ignored
        }
        
        missing = []
        for var in candidates:
            # Check if it is defined
            if var not in defined_vars:
                # Double check: maybe it's imported? 
                # For this simple test, we assume they must be in constants.py 
                # OR they are local variables. 
                # But SCREAMING_CASE usually implies global constant.
                missing.append(var)
        
        if missing:
            self.fail(f"Undefined constants in renderer.py: {missing}. Please add them to src/constants.py")

if __name__ == '__main__':
    unittest.main()

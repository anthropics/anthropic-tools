import unittest

from ..base_tool import BaseTool

class TestBaseTool(unittest.TestCase):
    def test_require_use_tool_method(self):
        with self.assertRaises(TypeError):
            class CustomTool(BaseTool):
                pass
            
            tool = CustomTool()

if __name__ == "__main__":
    unittest.main()
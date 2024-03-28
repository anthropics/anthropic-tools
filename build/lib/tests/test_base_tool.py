import unittest

from ..tools.base_tool import BaseTool

class TestBaseTool(unittest.TestCase):
    def setUp(self):
        self.test_tool_name = "convert_text_to_upper"
        self.test_tool_description = """Converts a string of text to all upper case."""
        self.test_tool_parameters = [
            {"name": "my_string", "type": "str", "description": "The string to be uppercased."} 
        ]

    def test_require_use_tool_method(self):
        with self.assertRaises(TypeError):
            class CustomTool(BaseTool):
                pass

            tool = CustomTool(self.test_tool_name, self.test_tool_description, self.test_tool_parameters)

    def test_instantiate_tool(self):
        class CustomTool(BaseTool):
            def use_tool(self, my_string):
                return my_string.upper()
        
        custom_tool = CustomTool(self.test_tool_name, self.test_tool_description, self.test_tool_parameters)
        self.assertIsNotNone(custom_tool)
        self.assertIsInstance(custom_tool, BaseTool)

    def test_use_tool_method(self):
        class CustomTool(BaseTool):
            def use_tool(self, my_string):
                return my_string.upper()
        
        custom_tool = CustomTool(self.test_tool_name, self.test_tool_description, self.test_tool_parameters)
        self.assertEqual("BANANA", custom_tool.use_tool("baNana"))

    def test_format_tool_for_claude_method(self):
        class CustomTool(BaseTool):
            def use_tool(self, my_string):
                return my_string.upper()
        
        custom_tool = CustomTool(self.test_tool_name, self.test_tool_description, self.test_tool_parameters)

        correct_format = (
            "<tool_description>\n"
            f"<tool_name>{self.test_tool_name}</tool_name>\n"
            "<description>\n"
            f"{self.test_tool_description}\n"
            "</description>\n"
            "<parameters>\n"
            "<parameter>\n"
            f"<name>{self.test_tool_parameters[0]['name']}</name>\n"
            f"<type>{self.test_tool_parameters[0]['type']}</type>\n"
            f"<description>{self.test_tool_parameters[0]['description']}</description>\n"
            "</parameter>\n"
            "</parameters>\n"
            "</tool_description>"
        )
        
        self.assertEqual(correct_format, custom_tool.format_tool_for_claude())

if __name__ == "__main__":
    unittest.main()
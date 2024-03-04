# This contains the code for our two-tool calculator example. You can also read about it in the getting started section of the ReadMe.
# The goal here is to demonstrate how the ToolUser class can be used to pass multiple tools to Claude at once. To demonstrate this, we will use a very simple example, multi-tool arithmetic.

# Let's say we want Claude to be able to perform accurate addition and subtraction. In reality, we could probably build a single big calculator tool that evaluates a range of expressions, but for the sake of demonstrating Claude using multiple tools, we will instead create a separate tool for each operation, one for addition and one for subtraction.

# Start by importing the necessary classes, BaseTool for defining our addition and subtraction tools, and ToolUser for using them.
from .tools.base_tool import BaseTool
from .tool_user import ToolUser

# Define our addition tool
class AdditionTool(BaseTool):
    """Adds together two numbers, a + b."""

    def use_tool(self, a, b):
        return a+b

# Define our subtraction tool
class SubtractionTool(BaseTool):
    """Subtracts one number from another, a - b."""

    def use_tool(self, a, b):
        return a-b

# Initialize an instance of each tool
addition_tool_name = "perform_addition"
addition_tool_description = """Add one number (a) to another (b), returning a+b.
Use this tool WHENEVER you need to perform any addition calculation, as it will ensure your answer is precise."""
addition_tool_parameters = [
    {"name": "a", "type": "float", "description": "The first number in your addition equation."},
    {"name": "b", "type": "float", "description": "The second number in your addition equation."}
]

subtraction_tool_name = "perform_subtraction"
subtraction_tool_description = """Subtract one number (b) from another (a), returning a-b.
Use this tool WHENEVER you need to perform any subtraction calculation, as it will ensure your answer is precise."""
subtraction_tool_parameters = [
    {"name": "a", "type": "float", "description": "The minuend in your subtraction equation."},
    {"name": "b", "type": "float", "description": "The subtrahend in your subtraction equation."}
]

addition_tool = AdditionTool(addition_tool_name, addition_tool_description, addition_tool_parameters)
subtraction_tool = SubtractionTool(subtraction_tool_name, subtraction_tool_description, subtraction_tool_parameters)

# Pass the tool instance into the ToolUser
tool_user = ToolUser([addition_tool, subtraction_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    messages = [{"role":"user", "content":"John has three apples. Maggie has nine apples. Tim has 4 bananas. If John gives Maggie 1 apple and Tim gives John 2 bananas, how much fruit does each person have?"}]
    print(tool_user.use_tools(messages, execution_mode="automatic"))
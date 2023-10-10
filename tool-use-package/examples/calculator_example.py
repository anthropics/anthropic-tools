from ..base_tool import BaseTool
from ..tool_user import ToolUser

# Define our custom calculator tool
class CalculatorTool(BaseTool):
    # TODO: Define a real calculator here.
    def use_tool(self, expression):
        return 45.75

# Initialize an instance of the tool by passing in tool_name, tool_description, and tool_parameters
tool_name = "evaluate_expression"
tool_description = """Evaluate mathematical expressions precisely using Python's math module.
- Supports any expression containing symbols such as *, /, +, -, and parentheses.
- Supports functions such as sin, cos, tan, factorial, sqrt, log, exp, and more. log can be given a base as a second argument like so: log(4,10).
- ** is used for exponentiation.
- Also supports constants such as pi and e.
Use this tool WHENEVER you need to perform any arithmetic calculation, as it will ensure your answer is precise."""
tool_parameters = [
    {"name": "expression", "type": "str", "description": "The math expression to evaluate, such as 2*6+(37-3)**3*log(7, 10)"}
]

my_calculator_tool = CalculatorTool(tool_name, tool_description, tool_parameters)

# Pass the tool instance into the ToolUser
my_tool_user = ToolUser([my_calculator_tool])

# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    print(my_tool_user.use_tools("A construction crew is building a wall that is 305 meters long and 3 meters high. If one worker can build 4 square meters per hour, how many total hours will it take 5 workers to build the wall?"))
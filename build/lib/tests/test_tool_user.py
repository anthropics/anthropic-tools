import unittest

from ..tool_user import ToolUser
from ..calculator_example import addition_tool, subtraction_tool
from ..prompt_constructors import construct_successful_function_run_injection_prompt, construct_error_function_run_injection_prompt

class TestToolUser(unittest.TestCase):
    def setUp(self):
        self.tool_user = ToolUser([addition_tool, subtraction_tool])
    
    def test_convert_value(self):
        self.assertEqual(self.tool_user._convert_value("['a', 'c', 'e']", "list"), ["a", "c", "e"])
        self.assertEqual(self.tool_user._convert_value("The big orange cat ran.", "str"), "The big orange cat ran.")
        self.assertEqual(self.tool_user._convert_value("3", "int"), 3)
        self.assertEqual(self.tool_user._convert_value("${get_current_user_id()}", "int"), "${get_current_user_id()}")
        with self.assertRaises(AttributeError):
            self.tool_user._convert_value("8", "canteloupe")

    def test_construct_injections(self):
        invoke_results_success = {"status": "SUCCESS", "invoke_results": [{"tool_name": "perform_addition", "tool_result": 8}, {"tool_name": "perform_addition", "tool_result": 4}, {"tool_name": "perform_subtraction", "tool_result": -3}]}
        invoke_results_error = {"status": "ERROR", "message": "No tool named <tool_name>perform_multiplication</tool_name> available."}
        self.assertEqual(self.tool_user._construct_next_injection(invoke_results_success), construct_successful_function_run_injection_prompt(invoke_results_success['invoke_results']))
        self.assertEqual(self.tool_user._construct_next_injection(invoke_results_error), construct_error_function_run_injection_prompt(invoke_results_error['message']))

    def test_function_calls_valid_format_and_invoke_extraction(self):
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<completion>I love to go waterskiing</completion>"), {"status": True, "invokes": []})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>305</a><b>300</b></parameters></invoke>"), {"status": False, "reason": "No valid <function_calls></function_calls> tags present in your query."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><tool_name>perform_addition<parameters><a>305</a><b>300</b></parameters></invoke></function_calls>"), {"status": False, "reason": "Missing <invoke></invoke> tags inside of <function_calls></function_calls> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke>perform_addition<parameters><a>305</a><b>300</b></parameters></invoke></function_calls>"), {"status": False, "reason": "Missing <tool_name></tool_name> tags inside of <invoke></invoke> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><tool_name></tool_name><parameters><a>305</a><b>300</b></parameters></invoke></function_calls>"), {"status": False, "reason": "More than one tool_name specified inside single set of <invoke></invoke> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>305</a><b>300</b></invoke></function_calls>"), {"status": False, "reason": "Missing <parameters></paraeters> tags inside of <invoke></invoke> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>305</a><b>300</b></parameters><parameters></parameters></invoke></function_calls>"), {"status": False, "reason": "More than one set of <parameters></parameters> tags specified inside single set of <invoke></invoke> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>305</a><b>300</b><c></parameters></invoke></function_calls>"), {"status": False, "reason": "Imbalanced tags inside <parameters></parameters> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>305</a><b>300</b><c><c></parameters></invoke></function_calls>"), {"status": False, "reason": "Non-matching opening and closing tags inside <parameters></parameters> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>305</a><b>300</b><c></d></parameters></invoke></function_calls>"), {"status": False, "reason": "Non-matching opening and closing tags inside <parameters></parameters> tags."})
        self.assertEqual(self.tool_user._function_calls_valid_format_and_invoke_extraction("<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>305</a><b>300</b></parameters></invoke></function_calls>"), {"status": True, "invokes": [{"tool_name": "perform_addition", "parameters_with_values": [("a", "305"), ("b", "300")]}], 'prefix_content': ''})

    def test_parse_function_calls(self):
        a = 300.0
        b = 305.0
        self.assertEqual(self.tool_user._parse_function_calls(f"some text that might go here<function_calls><invoke><tool_name>perform_addition</tool_name><parameters><a>{a}</a><b>{b}</b></parameters></invoke></function_calls>some more text that might go here...", True), {"status": "SUCCESS", "invoke_results": [{'tool_name': 'perform_addition', 'tool_result': addition_tool.use_tool(a, b)}], 'content': 'some text that might go here'})

if __name__ == "__main__":
    unittest.main()
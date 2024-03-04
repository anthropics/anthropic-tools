from anthropic import Anthropic
from anthropic_bedrock import AnthropicBedrock
import re
import builtins
import ast

from .prompt_constructors import construct_use_tools_prompt, construct_successful_function_run_injection_prompt, construct_error_function_run_injection_prompt, construct_prompt_from_messages
from .messages_api_converters import convert_completion_to_messages, convert_messages_completion_object_to_completions_completion_object

class ToolUser:
    """
    A class to interact with the Claude API while giving it the ability to use tools.
    
    Attributes:
    -----------
    - tools (list): A list of tool instances that this ToolUser instance can interact with. These tool instances should be subclasses of BaseTool.
    - temperature (float, optional): The temperature parameter to be passed to Claude. Default is 0.
    - max_retries (int, optional): The maximum number of times to retry in case of an error while interacting with a tool. Default is 3.
    - client: An instance of the Anthropic/AWS Bedrock API client. You must have set your Anthropic API Key or AWS Bedrock API keys as environment variables.
    - model: The name of the model (default Claude-2.1).
    - current_prompt (str): The current prompt being used in the interaction. Is added to as Claude interacts with tools.
    - current_num_retries (int): The current number of retries that have been attempted. Resets to 0 after a successful function call.
    
    Note/TODOs:
    -----
    The class interacts with the model using formatted prompts and expects the model to respond using specific XML tags.
    Certain characters such as angle brackets inside parameter values will currently break the class. These issues are called out in the code.

    Usage:
    ------
    To use this class, you should instantiate it with a list of tools (tool_user = ToolUser(tools)). You then interact with it as you would the normal claude API, by providing a prompt to tool_user.use_tools(prompt) and expecting a completion in return.
    """

    def __init__(self, tools, temperature=0, max_retries=3, first_party=True, model="default"):
        self.tools = tools
        self.temperature = temperature
        self.max_retries = max_retries
        self.first_party = first_party
        if first_party:
            if model == "default":
                self.model = "claude-3-opus-20240229"
            else:
                self.model=model
            self.client = Anthropic()
        else:
            if model == "anthropic.claude-v2:1" or model == "default":
                self.model = "anthropic.claude-v2:1"
            else:
                raise ValueError("Only Claude 2.1 is currently supported when working with bedrock in this sdk. If you'd like to use another model, please use the first party anthropic API (and set first_party=true).")
            self.client = AnthropicBedrock()
        self.current_prompt = None
        self.current_num_retries = 0

    
    def use_tools(self, messages, verbose=0, execution_mode="manual", max_tokens_to_sample=2000, temperature=1):
        """
        Main method for interacting with an instance of ToolUser. Calls Claude with the given prompt and tools and returns the final completion from Claude after using the tools.
        - mode (str, optional): If 'single_function', will make a single call to Claude and then stop, returning only a FunctionResult dataclass (atomic function calling). If 'agentic', Claude will continue until it produces an answer to your question and return a completion (agentic function calling). Defaults to True.
        """

        if execution_mode not in ["manual", "automatic"]:
            raise ValueError(f"Error: execution_mode must be either 'manual' or 'automatic'. Provided Value: {execution_mode}")
        
        prompt = ToolUser._construct_prompt_from_messages(messages)
        constructed_prompt = construct_use_tools_prompt(prompt, self.tools, messages[-1]['role'])
        # print(constructed_prompt)
        self.current_prompt = constructed_prompt
        if verbose == 1:
            print("----------CURRENT PROMPT----------")
            print(self.current_prompt)
        if verbose == 0.5:
            print("----------INPUT (TO SEE SYSTEM PROMPT WITH TOOLS SET verbose=1)----------")
            print(prompt)
        
        completion = self._complete(self.current_prompt, max_tokens_to_sample=max_tokens_to_sample, temperature=temperature)

        if completion.stop_reason == 'stop_sequence':
            if completion.stop == '</function_calls>': # Would be good to combine this with above if statement if completion.stop is guaranteed to be present
                formatted_completion = f"{completion.completion}</function_calls>"
            else:
                formatted_completion = completion.completion
        else:
            formatted_completion = completion.completion
        
        if verbose == 1:
            print("----------COMPLETION----------")
            print(formatted_completion)
        if verbose == 0.5:
            print("----------CLAUDE GENERATION----------")
            print(formatted_completion)
        
        if execution_mode == 'manual':
            parsed_function_calls = self._parse_function_calls(formatted_completion, False)
            if parsed_function_calls['status'] == 'DONE':
                res = {"role": "assistant", "content": formatted_completion}
            elif parsed_function_calls['status'] == 'ERROR':
                res = {"status": "ERROR", "error_message": parsed_function_calls['message']}
            elif parsed_function_calls['status'] == 'SUCCESS':
                res = {"role": "tool_inputs", "content": parsed_function_calls['content'], "tool_inputs": parsed_function_calls['invoke_results']}
            else:
                raise ValueError("Unrecognized status in parsed_function_calls.")
            
            return res
        
        while True:
            parsed_function_calls = self._parse_function_calls(formatted_completion, True)
            if parsed_function_calls['status'] == 'DONE':
                return formatted_completion
            
            claude_response = self._construct_next_injection(parsed_function_calls)
            if verbose == 0.5:
                print("----------RESPONSE TO FUNCTION CALLS (fed back into Claude)----------")
                print(claude_response)
            
            self.current_prompt = (
                f"{self.current_prompt}"
                f"{formatted_completion}\n\n"
                f"{claude_response}"
            )

            if verbose == 1:
                print("----------CURRENT PROMPT----------")
                print(self.current_prompt)
            
            completion = self._complete(self.current_prompt, max_tokens_to_sample=max_tokens_to_sample, temperature=temperature)

            if completion.stop_reason == 'stop_sequence':
                if completion.stop == '</function_calls>': # Would be good to combine this with above if statement if complaetion.stop is guaranteed to be present
                    formatted_completion = f"{completion.completion}</function_calls>"
                else:
                    formatted_completion = completion.completion
            else:
                formatted_completion = completion.completion
            
            if verbose == 1:
                print("----------CLAUDE GENERATION----------")
                print(formatted_completion)
            if verbose == 0.5:
                print("----------CLAUDE GENERATION----------")
                print(formatted_completion)


    
    def _parse_function_calls(self, last_completion, evaluate_function_calls):
        """Parses the function calls from the model's response if present, validates their format, and invokes them."""

        # Check if the format of the function call is valid
        invoke_calls = ToolUser._function_calls_valid_format_and_invoke_extraction(last_completion)
        if not invoke_calls['status']:
            return {"status": "ERROR", "message": invoke_calls['reason']}
        
        if not invoke_calls['invokes']:
            return {"status": "DONE"}
        
        # Parse the query's invoke calls and get it's results
        invoke_results = []
        for invoke_call in invoke_calls['invokes']:
            # Find the correct tool instance
            tool_name = invoke_call['tool_name']
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if tool is None:
                return {"status": "ERROR", "message": f"No tool named <tool_name>{tool_name}</tool_name> available."}
            
            # Validate the provided parameters
            parameters = invoke_call['parameters_with_values']
            parameter_names = [p['name'] for p in tool.parameters]
            provided_names = [p[0] for p in parameters]

            invalid = set(provided_names) - set(parameter_names)
            missing = set(parameter_names) - set(provided_names)
            if invalid:
                return {"status": "ERROR", "message": f"Invalid parameters {invalid} for <tool_name>{tool_name}</tool_name>."}
            if missing:
                return {"status": "ERROR", "message": f"Missing required parameters {parameter_names} for <tool_name>{tool_name}</tool_name>."}
            
            # Convert values and call tool
            converted_params = {}
            for name, value in parameters:
                param_def = next(p for p in tool.parameters if p['name'] == name)
                type_ = param_def['type']
                converted_params[name] = ToolUser._convert_value(value, type_)
            
            if not evaluate_function_calls:
                invoke_results.append({"tool_name": tool_name, "tool_arguments": converted_params})
            else:
                invoke_results.append({"tool_name": tool_name, "tool_result": tool.use_tool(**converted_params)})
        
        return {"status": "SUCCESS", "invoke_results": invoke_results, "content": invoke_calls['prefix_content']}
    
    def _construct_next_injection(self, invoke_results):
        """Constructs the next prompt based on the results of the previous function call invocations."""

        if invoke_results['status'] == 'SUCCESS':
            self.current_num_retries = 0
            return construct_successful_function_run_injection_prompt(invoke_results['invoke_results'])
        elif invoke_results['status'] == 'ERROR':
            if self.current_num_retries == self.max_retries:
                raise ValueError("Hit maximum number of retries attempting to use tools.")
            
            self.current_num_retries +=1
            return construct_error_function_run_injection_prompt(invoke_results['message'])
        else:
            raise ValueError(f"Unrecognized status from invoke_results, {invoke_results['status']}.")
    
    def _complete(self, prompt, max_tokens_to_sample, temperature):
        if self.first_party:
            return self._messages_complete(prompt, max_tokens_to_sample, temperature)
        else:
            return self._completions_complete(prompt, max_tokens_to_sample, temperature)
    
    def _messages_complete(self, prompt, max_tokens_to_sample, temperature):
        messages = convert_completion_to_messages(prompt)
        if 'system' not in messages:
            completion = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens_to_sample,
                temperature=temperature,
                stop_sequences=["</function_calls>", "\n\nHuman:"],
                messages=messages['messages']
            )
        else:
            completion = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens_to_sample,
                temperature=temperature,
                stop_sequences=["</function_calls>", "\n\nHuman:"],
                messages=messages['messages'],
                system=messages['system']
            )
        return convert_messages_completion_object_to_completions_completion_object(completion)

    def _completions_complete(self, prompt, max_tokens_to_sample, temperature):
        completion = self.client.completions.create(
            model=self.model,
            max_tokens_to_sample=max_tokens_to_sample,
            temperature=temperature,
            stop_sequences=["</function_calls>", "\n\nHuman:"],
            prompt=prompt
        )
        return completion
    
    @staticmethod
    def _function_calls_valid_format_and_invoke_extraction(last_completion):
        """Check if the function call follows a valid format and extract the attempted function calls if so. Does not check if the tools actually exist or if they are called with the requisite params."""
        
        # Check if there are any of the relevant XML tags present that would indicate an attempted function call.
        function_call_tags = re.findall(r'<function_calls>|</function_calls>|<invoke>|</invoke>|<tool_name>|</tool_name>|<parameters>|</parameters>', last_completion, re.DOTALL)
        if not function_call_tags:
            # TODO: Should we return something in the text to claude indicating that it did not do anything to indicate an attempted function call (in case it was in fact trying to and we missed it)?
            return {"status": True, "invokes": []}
        
        # Extract content between <function_calls> tags. If there are multiple we will only parse the first and ignore the rest, regardless of their correctness.
        match = re.search(r'<function_calls>(.*)</function_calls>', last_completion, re.DOTALL)
        if not match:
            return {"status": False, "reason": "No valid <function_calls></function_calls> tags present in your query."}
        
        func_calls = match.group(1)

        prefix_match = re.search(r'^(.*?)<function_calls>', last_completion, re.DOTALL)
        if prefix_match:
            func_call_prefix_content = prefix_match.group(1)
       
        # Check for invoke tags
        # TODO: Is this faster or slower than bundling with the next check?
        invoke_regex = r'<invoke>.*?</invoke>'
        if not re.search(invoke_regex, func_calls, re.DOTALL):
            return {"status": False, "reason": "Missing <invoke></invoke> tags inside of <function_calls></function_calls> tags."}
       
        # Check each invoke contains tool name and parameters
        invoke_strings = re.findall(invoke_regex, func_calls, re.DOTALL)
        invokes = []
        for invoke_string in invoke_strings:
            tool_name = re.findall(r'<tool_name>.*?</tool_name>', invoke_string, re.DOTALL)
            if not tool_name:
                return {"status": False, "reason": "Missing <tool_name></tool_name> tags inside of <invoke></invoke> tags."}
            if len(tool_name) > 1:
                return {"status": False, "reason": "More than one tool_name specified inside single set of <invoke></invoke> tags."}

            parameters = re.findall(r'<parameters>.*?</parameters>', invoke_string, re.DOTALL)
            if not parameters:
                return {"status": False, "reason": "Missing <parameters></paraeters> tags inside of <invoke></invoke> tags."}
            if len(parameters) > 1:
                return {"status": False, "reason": "More than one set of <parameters></parameters> tags specified inside single set of <invoke></invoke> tags."}
            
            # Check for balanced tags inside parameters
            # TODO: This will fail if the parameter value contains <> pattern or if there is a parameter called parameters. Fix that issue.
            tags = re.findall(r'<.*?>', parameters[0].replace('<parameters>', '').replace('</parameters>', ''), re.DOTALL)
            if len(tags) % 2 != 0:
                return {"status": False, "reason": "Imbalanced tags inside <parameters></parameters> tags."}
            
            # Loop through the tags and check if each even-indexed tag matches the tag in the position after it (with the / of course). If valid store their content for later use.
            # TODO: Add a check to make sure there aren't duplicates provided of a given parameter.
            parameters_with_values = []
            for i in range(0, len(tags), 2):
                opening_tag = tags[i]
                closing_tag = tags[i+1]
                closing_tag_without_second_char = closing_tag[:1] + closing_tag[2:]
                if closing_tag[1] != '/' or opening_tag != closing_tag_without_second_char:
                    return {"status": False, "reason": "Non-matching opening and closing tags inside <parameters></parameters> tags."}
                
                parameters_with_values.append((opening_tag[1:-1], re.search(rf'{opening_tag}(.*?){closing_tag}', parameters[0], re.DOTALL).group(1)))
        
            # Parse out the full function call
            invokes.append({"tool_name": tool_name[0].replace('<tool_name>', '').replace('</tool_name>', ''), "parameters_with_values": parameters_with_values})
        
        return {"status": True, "invokes": invokes, "prefix_content": func_call_prefix_content}
    
    # TODO: This only handles the outer-most type. Nested types are an unimplemented issue at the moment.
    @staticmethod
    def _convert_value(value, type_str):
        """Convert a string value into its appropriate Python data type based on the provided type string.

        Arg:
            value: the value to convert
            type_str: the type to convert the value to

        Returns:
            The value converted into the requested type or the original value
            if the conversion failed.
        """

        if type_str in ("list", "dict"):
            return ast.literal_eval(value)
        
        type_class = getattr(builtins, type_str)
        try:
            return type_class(value)
        except ValueError:
            return value

    @staticmethod
    def _construct_prompt_from_messages(messages):
        return construct_prompt_from_messages(messages)

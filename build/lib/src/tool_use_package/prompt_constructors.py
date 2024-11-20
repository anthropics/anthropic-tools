import typing

# This file contains prompt constructors for various pieces of code. Used primarily to keep other code legible.
def construct_tool_use_system_prompt(tools):
    tool_use_system_prompt = (
        "In this environment you have access to a set of tools you can use to answer the user's question.\n"
        "\n"
        "You may call them like this:\n"
        "<function_calls>\n"
        "<invoke>\n"
        "<tool_name>$TOOL_NAME</tool_name>\n"
        "<parameters>\n"
        "<$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>\n"
        "...\n"
        "</parameters>\n"
        "</invoke>\n"
        "</function_calls>\n"
        "\n"
        "Here are the tools available:\n"
        "<tools>\n"
        + '\n'.join([tool.format_tool_for_claude() for tool in tools]) +
        "\n</tools>"
    )
        
    return tool_use_system_prompt

def construct_use_tools_prompt(prompt, tools, last_message_role):
    if last_message_role == 'user':
        constructed_prompt = (
            f"{construct_tool_use_system_prompt(tools)}"
            f"{prompt}"
            "\n\nAssistant:"
        )
    else:
        constructed_prompt = (
            f"{construct_tool_use_system_prompt(tools)}"
            f"{prompt}"
        )
    
    return constructed_prompt

def construct_successful_function_run_injection_prompt(invoke_results_results):
    constructed_prompt = (
        "<function_results>\n"
        + '\n'.join(f"<result>\n<tool_name>{res['tool_name']}</tool_name>\n<stdout>\n{res['tool_result']}\n</stdout>\n</result>" for res in invoke_results_results) +
        "\n</function_results>"
        )
    
    return constructed_prompt

def construct_error_function_run_injection_prompt(invoke_results_error_message):
    constructed_prompt = (
         "<function_results>\n"
         "<system>\n"
         f"{invoke_results_error_message}"
         "\n</system>"
         "\n</function_results>"
    )

    return constructed_prompt

def construct_format_parameters_prompt(parameters):
    constructed_prompt = "\n".join(f"<parameter>\n<name>{parameter['name']}</name>\n<type>{parameter['type']}</type>\n<description>{parameter['description']}</description>\n</parameter>" for parameter in parameters)

    return constructed_prompt


def construct_format_tool_for_claude_prompt(name, description, parameters):
    constructed_prompt = (
        "<tool_description>\n"
        f"<tool_name>{name}</tool_name>\n"
        "<description>\n"
        f"{description}\n"
        "</description>\n"
        "<parameters>\n"
        f"{construct_format_parameters_prompt(parameters)}\n"
        "</parameters>\n"
        "</tool_description>"
    )

    return constructed_prompt

def construct_format_sql_tool_for_claude_prompt(name, description, parameters, db_schema, db_dialect):
    constructed_prompt = (
        "<tool_description>\n"
        f"<tool_name>{name}</tool_name>\n"
        "<description>\n"
        f"{description}\n"
        f"The database uses {db_dialect} dialect. The schema of the database is provided to you here:\n"
        "<schema>\n"
        f"{db_schema}\n"
        "</schema>\n"
        "</description>\n"
        "<parameters>\n"
        f"{construct_format_parameters_prompt(parameters)}\n"
        "</parameters>\n"
        "<important_usage_notes>\n"
        "* When invoking this tool, the contents of the 'query' parameter does NOT need to be XML-escaped.\n"
        "</important_usage_notes>\n"
        "</tool_description>"
    )

    return constructed_prompt

# Collection of constructors for going from conversation list to prompt string
def construct_prompt_from_messages(messages):
    validate_messages(messages)
    
    constructed_prompt = ""
    for i, message in enumerate(messages):
        if message['role'] == 'user':
            if (i > 0 and messages[i-1]['role'] != 'user') or i == 0:
                constructed_prompt = f"{constructed_prompt}\n\nHuman: {message['content']}"
            else:
                constructed_prompt = f"{constructed_prompt}\n\n{message['content']}"
        if message['role'] == 'assistant':
            if (i > 0 and messages[i-1]['role'] == 'user') or i == 0:
                constructed_prompt = f"{constructed_prompt}\n\nAssistant: {message['content']}"
            else:
                constructed_prompt = f"{constructed_prompt}\n\n{message['content']}"
        if message['role'] == 'tool_inputs':
            appendage = construct_tool_inputs_message(message['content'], message['tool_inputs'])
            if (i > 0 and messages[i-1]['role'] == 'user') or i == 0:
                constructed_prompt = f"{constructed_prompt}\n\nAssistant:{appendage}"
            elif message['content'] == "":
                constructed_prompt = f"{constructed_prompt}{appendage}"
            else:
                constructed_prompt = f"{constructed_prompt}\n\n{appendage}"
        if message['role'] == 'tool_outputs':
            appendage = construct_tool_outputs_message(message['tool_outputs'], message['tool_error'])
            if (i > 0 and messages[i-1]['role'] == 'user') or i == 0:
                constructed_prompt = f"{constructed_prompt}\n\nAssistant:{appendage}"
            else:
                constructed_prompt = f"{constructed_prompt}{appendage}"
    
    return constructed_prompt

def validate_messages(messages):
    if not isinstance(messages, list):
        raise ValueError("Messages must be a list of length > 0.")
    if len(messages) < 1:
        raise ValueError("Messages must be a list of length > 0.")
    
    valid_roles = ['user', 'assistant', 'tool_inputs', 'tool_outputs']
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("All messages in messages list should be dictionaries.")
        if 'role' not in message:
            raise ValueError("All messages must have a 'role' key.")
        if message['role'] not in valid_roles:
            raise ValueError(f"{message['role']} is not a valid role. Valid roles are {valid_roles}")
        if message['role'] == 'user' or message['role'] == 'assistant':
            if 'content' not in message:
                raise ValueError("All messages with user or assistant roles must have a 'content' key.")
            if not isinstance(message['content'], str):
                raise ValueError("For messages with role='user' or role='assistant', content must be a string.")
        if message['role'] == 'tool_inputs':
            if 'tool_inputs' not in message:
                raise ValueError("All messages with tool_inputs roles must have a 'tool_inputs' key.")
            if not isinstance(message['tool_inputs'], list):
                raise ValueError("For messages with role='tool_inputs', tool_inputs must be a list of length > 0.")
            if len(message['tool_inputs']) < 1:
                raise ValueError("For messages with role='tool_inputs', tool_inputs must be a list of length > 0.")
            for tool_input in message['tool_inputs']:
                if not isinstance(tool_input, dict):
                    raise ValueError("All elements of tool_inputs must be dictionaries with keys 'tool_name' and 'tool_arguments'.")
                if 'tool_name' not in tool_input:
                    raise ValueError("All elements of tool_inputs must be dictionaries with keys 'tool_name' and 'tool_arguments'.")
                if 'tool_arguments' not in tool_input:
                    raise ValueError("All elements of tool_inputs must be dictionaries with keys 'tool_name' and 'tool_arguments'.")
        if message['role'] == 'tool_outputs':
            if 'content' in message:
                raise ValueError("tool_outputs should not have a 'content' key/value pair")
            if message['tool_error'] is not None and message['tool_outputs'] is not None:
                raise ValueError("Only one of tool_outputs and tool_error should be provided, the other should be None. Both are currently not None.")
            if message['tool_error'] is None and message['tool_outputs'] is None:
                raise ValueError("For messages with role='tool_putput' you must provide one of tool_outputs or tool_error.")
            if message['tool_outputs'] is not None and not isinstance(message['tool_outputs'], list):
                raise ValueError("tool_error must be str or None.")
            if message['tool_error'] is not None and not isinstance(message['tool_error'], str):
                raise ValueError("tool_error must be str or None.")

def construct_tool_inputs_message(content, tool_inputs):
    def format_parameters(tool_arguments):
        return '\n'.join([f'<{key}>{value}</{key}>' for key, value in tool_arguments.items()])
    
    single_call_messages = "\n\n".join([f"<invoke>\n<tool_name>{tool_input['tool_name']}</tool_name>\n<parameters>\n{format_parameters(tool_input['tool_arguments'])}\n</parameters>\n</invoke>"for tool_input in tool_inputs])
    message = (
        f"{content}"
        "\n\n<function_calls>\n"
        f"{single_call_messages}\n"
        "</function_calls>"
    )
    return message

def construct_tool_outputs_message(tool_outputs, tool_error):
    if tool_error is not None:
        message = construct_error_function_run_injection_prompt(tool_error)
        return f"\n\n{message}"
    elif tool_outputs is not None:
        message = construct_successful_function_run_injection_prompt(tool_outputs)
        return f"\n\n{message}"
    else:
        raise ValueError("At least one of tool_result or tool_error must not be None.")
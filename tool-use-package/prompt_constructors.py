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

def construct_use_tools_prompt(prompt, tools):
    constructed_prompt = (
        f"{construct_tool_use_system_prompt(tools)}"
        "\n\nHuman: "
        f"{prompt}"
        "\n\nAssistant:"
    )

    return constructed_prompt

def construct_successful_function_run_injection_prompt(invoke_results_results):
    constructed_prompt = (
        "<function_results>\n"
        + '\n'.join(f"<result>\n<tool_name>{res[0]}</tool_name>\n<stdout>\n{res[1]}\n</stdout>\n</result>" for res in invoke_results_results) +
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
    constructed_prompt = "\n".join([f"<parameter>\n<name>{parameter['name']}</name>\n<type>{parameter['type']}</type>\n<description>{parameter['description']}</description>\n</parameter>" for parameter in parameters])

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
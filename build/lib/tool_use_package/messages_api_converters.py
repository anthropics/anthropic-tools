def convert_completion_to_messages(completion):
    result = {"messages": []}
    
    parts = completion.split('\n\nHuman:')
    if len(parts) < 2:
        raise ValueError("No human message found in the completion")
    
    # Assign the first part as the system message
    result["system"] = parts[0].strip()
    
    # Process the remaining parts
    for i in range(1, len(parts)):
        content_parts = parts[i].split('\n\nAssistant:', 1)

        result["messages"].append({"role": "user", "content": content_parts[0].strip()})
        
        if len(content_parts) == 2:
            result["messages"].append({"role": "assistant", "content": content_parts[1].strip()})
        elif len(content_parts) > 2:
            # If there are more than two parts, it means there are consecutive assistant messages
            raise ValueError("Consecutive assistant messages found")
        elif i < len(parts) - 1:
            # If there is no assistant message and it's not the last part, raise an error for consecutive human messages
            raise ValueError("Consecutive human messages found")
    
    return result

class MiniCompletion:
    def __init__(self, stop_reason, stop, completion):
        self.stop_reason = stop_reason
        self.stop = stop
        self.completion = completion


def convert_messages_completion_object_to_completions_completion_object(message):
    if message.stop_reason == 'end_turn':
        stop_reason = 'stop_sequence'
    elif message.stop_reason == 'stop_sequence':
        stop_reason = 'stop_sequence'
    else:
        stop_reason =  message.stop_reason

    if message.stop_sequence is None:
        stop_sequence = '\n\nHuman:'
    else:
        stop_sequence = message.stop_sequence

    if message.content:
        if message.content[0].text:
            content = message.content[0].text
    else:
        content=''

    return MiniCompletion(
        stop_reason=stop_reason,
        stop=stop_sequence,
        completion=content
    )
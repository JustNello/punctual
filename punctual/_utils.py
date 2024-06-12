import os
import re


def parse_environment_variable(env_string):
    # Define the regular expression to match the pattern ${VARIABLE_NAME}
    pattern = r"\${(\w+)}"

    # Search for the pattern in the input string
    match = re.search(pattern, env_string)

    if match:
        # Extract the variable name from the matched group
        variable_name = match.group(1)

        # Retrieve the value of the environment variable
        variable_value = os.getenv(variable_name)

        # Return the value of the environment variable
        return variable_value

    # If no match is found, return None or handle accordingly
    return None

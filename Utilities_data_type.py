from enum import Enum

# Mother class representing id_script
class IdScript:

    # Class for the 'execution' category
    class Execution(Enum):
        INPUT_ARGS = 0  # corresponds to 'input_args'
        OUTPUT_RESULT = 1  # corresponds to 'output_result'

        # Method to return the id_category
        @staticmethod
        def id_category():
            return 0  # id_category for 'execution'

    # Class for the 'runtime' category
    class Runtime(Enum):
        METADATA = 0  # corresponds to 'metadata'
        SERVICE_FUNCTION = 1  # corresponds to 'service_function'

        # Method to return the id_category
        @staticmethod
        def id_category():
            return 1  # id_category for 'runtime'

    # Class for the 'error_handling' category
    class ErrorHandling(Enum):
        INPUT_DATA = 0  # corresponds to 'input_data'
        METADATA_DATA = 1  # corresponds to 'metadata_data'

        # Method to return the id_category
        @staticmethod
        def id_category():
            return 2  # id_category for 'error_handling'


# Example of accessing the id_type values directly (no casting)
print(IdScript.Execution.INPUT_ARGS.value)          # Output: 0 (id_type)
print(IdScript.Runtime.METADATA.value)              # Output: 0 (id_type)
print(IdScript.ErrorHandling.INPUT_DATA.value)      # Output: 0 (id_type)

# Example of accessing the id_category directly (no casting)
print(IdScript.Execution.id_category())      # Output: 0 (id_category for Execution)
print(IdScript.Runtime.id_category())        # Output: 1 (id_category for Runtime)
print(IdScript.ErrorHandling.id_category())  # Output: 2 (id_category for ErrorHandling)

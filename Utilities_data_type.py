from enum import Enum

# Base class to handle multiple id_scripts
class IdScript:

    # id_script 0
    class IdScript0:

        # Class for the 'execution' category
        class Execution(Enum):
            INPUT_ARGS = 0  # corresponds to 'input_args'
            OUTPUT_RESULT = 1  # corresponds to 'output_result'

            @staticmethod
            def id_category():
                return 0  # id_category for 'execution'

        # Class for the 'runtime' category
        class Runtime(Enum):
            METADATA = 0  # corresponds to 'metadata'
            SERVICE_FUNCTION = 1  # corresponds to 'service_function'

            @staticmethod
            def id_category():
                return 1  # id_category for 'runtime'

        # Class for the 'error_handling' category
        class ErrorHandling(Enum):
            INPUT_DATA = 0  # corresponds to 'input_data'
            METADATA_DATA = 1  # corresponds to 'metadata_data'

            @staticmethod
            def id_category():
                return 2  # id_category for 'error_handling'

    # id_script 1 (with different id_category and id_type values)
    class IdScript1:

        # Class for the 'execution' category
        class Execution(Enum):
            INPUT_ARGS = 0  # corresponds to 'input_args'
            PROCESS_RESULT = 1  # corresponds to a different operation result

            @staticmethod
            def id_category():
                return 0  # id_category for 'execution' (same category index, different type)

        # Class for the 'runtime' category
        class Runtime(Enum):
            METADATA = 0  # corresponds to 'metadata'
            DIFFERENT_FUNCTION = 1  # another type name for id_script=1

            @staticmethod
            def id_category():
                return 1  # id_category for 'runtime'

        # Class for the 'error_handling' category
        class ErrorHandling(Enum):
            INPUT_DATA = 0  # corresponds to 'input_data'
            NEW_METADATA_DATA = 1  # another error handling type for id_script=1

            @staticmethod
            def id_category():
                return 2  # id_category for 'error_handling'

# Usage Example for id_script=0
print("id_script=0")
print(IdScript.IdScript0.Execution.INPUT_ARGS.value)          # Output: 0 (id_type for id_script=0)
print(IdScript.IdScript0.Runtime.METADATA.value)              # Output: 0 (id_type for id_script=0)
print(IdScript.IdScript0.ErrorHandling.INPUT_DATA.value)      # Output: 0 (id_type for id_script=0)

print(IdScript.IdScript0.Execution.id_category())             # Output: 0 (id_category for Execution in id_script=0)
print(IdScript.IdScript0.Runtime.id_category())               # Output: 1 (id_category for Runtime in id_script=0)
print(IdScript.IdScript0.ErrorHandling.id_category())         # Output: 2 (id_category for ErrorHandling in id_script=0)

# Usage Example for id_script=1 (different id_script with different id_type values)
print("\nid_script=1")
print(IdScript.IdScript1.Execution.INPUT_ARGS.value)          # Output: 0 (id_type for id_script=1)
print(IdScript.IdScript1.Runtime.METADATA.value)              # Output: 0 (id_type for id_script=1)
print(IdScript.IdScript1.ErrorHandling.INPUT_DATA.value)      # Output: 0 (id_type for id_script=1)

print(IdScript.IdScript1.Execution.id_category())             # Output: 0 (id_category for Execution in id_script=1)
print(IdScript.IdScript1.Runtime.id_category())               # Output: 1 (id_category for Runtime in id_script=1)
print(IdScript.IdScript1.ErrorHandling.id_category())         # Output: 2 (id_category for ErrorHandling in id_script=1)

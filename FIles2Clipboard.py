import os
import pyperclip


def Files2Clipboard(path, file_extension, subdirectories=False):
    """
    Copies the contents of text files within a specified directory (and optionally its subdirectories) to the clipboard.

    Parameters:
    - path (str): The path to the directory containing the files.
    - file_extension (str): The file extension to filter files by (e.g., '.txt'). Use '.*' to include all files.
    - subdirectories (bool, optional): Whether to include subdirectories in the search. Defaults to False.
    """
    content_to_copy = ""

    def read_files_in_directory(directory_path, root_label):
        nonlocal content_to_copy
        for file in os.listdir(directory_path):
            if file_extension == ".*" or file.endswith(file_extension):
                file_path = os.path.join(directory_path, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                        content_to_copy += (
                            f"This is {root_label}{file}:\n{file_content}\n\n"
                        )
                        print(f"Reading file: {file_path}")
                except Exception as e:
                    print(f"Could not read {file_path} as text: {e}")

    if subdirectories:
        # Run the tree command to get the directory structure
        tree_command = f'tree "{path}" /F'
        try:
            tree_output = os.popen(tree_command).read()
            content_to_copy += f"Directory tree of {path}:\n{tree_output}\n\n"
        except Exception as e:
            print(f"Could not generate directory tree: {e}")

        # Walk through the directory and its subdirectories
        for root, dirs, files in os.walk(path):
            # Filter out __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git')]
            root_label = f"./{os.path.relpath(root, path)}/" if root != path else "./"
            read_files_in_directory(root, root_label)
    else:
        read_files_in_directory(path, "./")

    if content_to_copy:
        pyperclip.copy(content_to_copy)
        line_count = content_to_copy.count('\n')
        print(f"All contents copied to clipboard [{line_count} lines].")
    else:
        print("No text files found to copy to clipboard.")


if __name__ == "__main__":
    path = os.getcwd()  # Use the current working directory
    file_extension = ".*"  # Use all files by default
    subdirectories = True  # Include subdirectories by default
    Files2Clipboard(path, file_extension, subdirectories)

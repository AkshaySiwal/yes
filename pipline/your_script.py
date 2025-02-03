import os

def main():
    # Reading Jenkins parameters
    selection_type = os.environ.get('SELECTION_TYPE')

    if selection_type == 'Manual':
        account = os.environ.get('ACCOUNT')
        role = os.environ.get('ROLE')
        print(f"Running in Manual mode with Account: {account} and Role: {role}")

    elif selection_type == 'File':
        file_path = os.environ.get('FILE_PATH')
        print(f"Running in File mode with file: {file_path}")
        # Add your file processing logic here
        with open(file_path, 'r') as file:
            content = file.read()
            print(f"File content: {content}")

if __name__ == "__main__":
    main()

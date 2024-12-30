import os
import subprocess

def get_git_ignored_files(directory):
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--others', '--ignored', '--exclude-standard', '--directory'],
            cwd=directory,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        ignored_files = result.stdout.splitlines()
        return ignored_files
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return []

def is_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            file.read()
        return True
    except:
        return False

def classify_files(directory):
    ignored_files = get_git_ignored_files(directory)
    classified_files = {'text_files': [], 'ignored_files': []}

    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            relative_path = os.path.relpath(filepath, directory)

            if relative_path in ignored_files:
                classified_files['ignored_files'].append(relative_path)
            elif is_text_file(filepath):
                classified_files['text_files'].append(relative_path)
            else:
                classified_files['ignored_files'].append(relative_path)

    return classified_files

# Example usage
directory = '.'
classified_files = classify_files(directory)
print("Text files:", classified_files['text_files'])
#print("Ignored files:", classified_files['ignored_files'])
import os
import zipfile

# Paths to the files and folders you want to include in the zip
file_paths = [
    'dashboard.py',
    'Procfile',
    'requirements.txt',
    'auth.yaml',
    'utils',  # Folder
    'prepare_data.py',
    '.ebextensions'  # Folder
]

# Create a zip file
with zipfile.ZipFile('app.zip', 'w') as zipf:
    for file_path in file_paths:
        if os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(file_path, '..')))
        else:
            zipf.write(file_path)

# Set the path for storing uploaded files
import os
import shutil


def delete_and_recreate_dir(path):
    # Delete the folder together with all the files
    if os.path.exists(path):
        shutil.rmtree(path)
    # Recreate the folder
    os.makedirs(path)


# Get file name without extension. Example: a/b/c.txt -> c
def get_file_name_from_path(path):
    return os.path.splitext(os.path.split(path)[1])[0]


# Get folder path from full path. Example: a/b/c.txt -> a/b
def get_folder_from_path(path):
    return os.path.split(path)[0]

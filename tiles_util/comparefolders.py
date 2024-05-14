import os
import argparse

def list_files_in_folder(folder):
    file_list = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_list.append(os.path.relpath(os.path.join(root, file), start=folder))
    return set(file_list)

def compare_folders(folder1, folder2):
    files1 = list_files_in_folder(folder1)
    files2 = list_files_in_folder(folder2)

    if files1 != files2:
        print("Differences in files:")
        print("Only in", folder1 + ":")
        print(files1 - files2)
        # print("Only in", folder2 + ":")
        # print(files2 - files1)
    else:
        print("Files are the same.")

    num_files1 = len(files1)
    num_files2 = len(files2)
    if num_files1 != num_files2:
        print("Total number of files is different.")
        print("Number of files in", folder1 + ":", num_files1)
        print("Number of files in", folder2 + ":", num_files2)
    else:
        print("Total number of files is the same: ", num_files1)

def main():
    parser = argparse.ArgumentParser(description="Compare two folders.")
    parser.add_argument("folder1", help="Path to the first folder")
    parser.add_argument("folder2", help="Path to the second folder")
    args = parser.parse_args()

    folder1 = args.folder1
    folder2 = args.folder2
    compare_folders(folder1, folder2)

if __name__ == "__main__":
    main()

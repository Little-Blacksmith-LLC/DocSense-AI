#!/bin/bash

# Script: cat_src_files.sh
# Usage: ./cat_src_files.sh <list_of_filepaths.txt>
#
# What it does:
# - Reads a text file (one file path per line; can be relative or absolute)
# - First lists the current directory (.)
# - For EACH file path in the list:
#   - Traverses EVERY subdirectory level in that file's path and runs "ls" on it
#   - Then runs "cat" on the actual file
# - Handles both relative paths (starts from .) and absolute paths (starts from /)
# - Continues even if some ls or cat fails (shows the natural error messages)

if [ $# -ne 1 ]; then
    echo "Usage: $0 <text_file_with_filepaths>"
    echo "Example: $0 my_files.txt"
    exit 1
fi

LIST_FILE="$1"

if [ ! -f "$LIST_FILE" ]; then
    echo "Error: File '$LIST_FILE' not found!"
    exit 1
fi

echo "============================================"
echo "Initial listing of the current directory:"
ls
echo "============================================"

# Function to traverse and ls every directory level up to the file's parent dir
traverse_directories() {
    local target="$1"  # This is dirname of the file path

    echo "Traversing path to parent directory: $target"

    if [[ "$target" == /* ]]; then
        # Absolute path → start at root
        echo "Listing: /"
        ls "/"
    else
        # Relative path → start at current directory
        echo "Listing: ."
        ls "."
    fi

    # Split the path into components (remove leading / for splitting)
    local clean_target="${target#/}"
    IFS='/' read -ra parts <<< "$clean_target"

    local prefix
    if [[ "$target" == /* ]]; then
        prefix="/"
    else
        prefix="."
    fi

    for part in "${parts[@]}"; do
        if [ -n "$part" ]; then
            if [ "$prefix" = "/" ]; then
                prefix="/$part"
            else
                prefix="$prefix/$part"
            fi
            echo "Listing subdirectory: $prefix"
            ls "$prefix"
        fi
    done
}

# Main loop: process each line in the list file
while IFS= read -r filepath || [ -n "$filepath" ]; do
    # Skip empty lines
    [ -z "$filepath" ] && continue

    echo ""
    echo "============================================"
    echo "Start: $filepath"
    echo "============================================"

    # Get the directory that contains the file
    parent_dir="$(dirname "$filepath")"

    # Traverse and ls every level
    traverse_directories "$parent_dir"

    # Now cat the file itself
    echo ""
    echo "Cat operation on $filepath:"
    echo "--------------------------------------------"
    cat "$filepath"
    echo "--------------------------------------------"
    echo "End: $filepath"
    echo "============================================"

done < "$LIST_FILE"

echo ""


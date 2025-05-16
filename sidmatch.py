#!/usr/bin/env python3
"""
sidmatch.py - Compare two CSV files and extract common or unique student ID numbers (SIDs).

Requested: 2025-05-10
How to run:
    python3 sidmatch.py

This script interactively prompts for two CSV files and attempts to extract SIDs from each, either
by column or from filenames embedded in the CSV. It then compares the resulting SID sets and offers
to save common or unique SIDs to output files.

- SIDs are normalized (leading '00' stripped).
- Null/malformed rows are logged to error.log.
- User is prompted before overwriting output files.
- Bash-style tab-completion is enabled for file path inputs.
- First 4 rows of each input file are displayed in aligned table format.
- All yes/no prompts now require explicit 'y' or 'n' input.
- Column prompts use 1-based numbering for user convenience.
"""

import csv
import os
import re
import sys
import readline

VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.pdf'}

# -------- Bash-style tab-completion --------

def path_completer(text, state):
    """
    Bash-style tab completion for files and directories, including nested paths and filenames.
    """
    text = os.path.expanduser(os.path.expandvars(text))

    if os.path.sep not in text:
        search_dir = '.'
        prefix = text
    else:
        search_dir, prefix = os.path.split(text)
        if not search_dir:
            search_dir = '.'

    try:
        entries = os.listdir(search_dir)
    except Exception:
        entries = []

    matches = []
    for entry in entries:
        if entry.startswith(prefix):
            full_path = os.path.join(search_dir, entry)
            display = os.path.join(search_dir, entry)
            if os.path.isdir(full_path):
                display += '/'
            matches.append(display)

    matches.sort()
    return matches[state] if state < len(matches) else None

def input_with_path_completion(prompt_text):
    readline.set_completer_delims(' \t\n')  # allow slashes
    readline.set_completer(path_completer)
    readline.parse_and_bind("tab: complete")
    try:
        return input(prompt_text)
    finally:
        readline.set_completer(None)

# -------- Prompt utilities --------

def prompt_file(prompt_text):
    while True:
        path = input_with_path_completion(prompt_text).strip()
        path = os.path.expanduser(os.path.expandvars(path))
        if os.path.isfile(path):
            return path
        print("File not found. Please try again.")

def prompt_column(prompt_text):
    while True:
        col_input = input(prompt_text).strip()
        if col_input.isdigit():
            n = int(col_input)
            if n >= 0:
                return n - 1 if n > 0 else -1
        print("Please enter a whole number: 1 for first column, 2 for second, etc., or 0 for none.")

def prompt_yes_no(prompt_text):
    while True:
        choice = input(prompt_text + " [y/n]: ").strip().lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        else:
            print("Please enter 'y' or 'n'.")

def validate_sid(s):
    return re.fullmatch(r'(?:00)?\d{7}', s) is not None

def extract_sid_from_filename(text):
    match = re.search(r'\b00\d{7}\b', text)
    return match.group(0) if match else None

def looks_like_valid_filename(value):
    if not value:
        return False
    ext = os.path.splitext(value)[1].lower()
    return ext in VALID_IMAGE_EXTENSIONS and extract_sid_from_filename(value) is not None

def prompt_output_filename(default_name):
    while True:
        name = input_with_path_completion(f"Enter output filename (default: {default_name}): ").strip()
        if not name:
            name = default_name
        name = os.path.expanduser(os.path.expandvars(name))
        if os.path.exists(name):
            if not prompt_yes_no(f"File '{name}' exists. Overwrite?"):
                continue
        return name

def write_sid_list(sid_set, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        for sid in sorted(sid_set):
            writer.writerow([sid])
    print(f"Wrote {len(sid_set)} SIDs to {output_file}")

# -------- SID extraction --------

def extract_sids_from_csv(path, file_label):
    print(f"\n--- Previewing first 4 rows of {file_label} ---")
    with open(path, newline='') as preview_file:
        reader = csv.reader(preview_file)
        preview_rows = [row for _, row in zip(range(4), reader)]

    if not preview_rows:
        print("(file is empty)")
    else:
        num_cols = max(len(row) for row in preview_rows)
        col_widths = [0] * num_cols
        for row in preview_rows:
            for i in range(len(row)):
                col_widths[i] = max(col_widths[i], len(row[i]))

        header = [f"[{i+1}]" for i in range(num_cols)]
        header_line = " | ".join(header[i].ljust(col_widths[i]) for i in range(num_cols))
        print(header_line)
        print("-" * len(header_line))

        for row in preview_rows:
            padded = [
                row[i].ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i])
                for i in range(num_cols)
            ]
            print(" | ".join(padded))

    print(f"\n--- Extracting SIDs from {file_label} ---")
    has_header = prompt_yes_no("Does the file have a header row?")

    while True:
        sid_col = prompt_column("Enter column number with raw SIDs (enter 0 if none): ")
        if sid_col == -1:
            break
        with open(path, newline='') as f:
            reader = csv.reader(f)
            if has_header:
                next(reader, None)
            if any(validate_sid(row[sid_col].strip()) for row in reader if len(row) > sid_col):
                sids = set()
                total_lines = 0
                error_log = open("error.log", "a")
                with open(path, newline='') as f:
                    reader = csv.reader(f)
                    if has_header:
                        next(reader, None)
                    for row in reader:
                        total_lines += 1
                        try:
                            if len(row) <= sid_col:
                                raise ValueError("Row too short")
                            sid = row[sid_col].strip()
                            if not validate_sid(sid):
                                raise ValueError(f"Invalid SID format: {sid}")
                            norm_sid = sid.lstrip("0")
                            sids.add(norm_sid)
                        except Exception as e:
                            error_log.write(f"{file_label} line {total_lines}: {e}\n")
                error_log.close()
                print(f"Total lines processed from {file_label}: {total_lines}")
                print(f"Unique valid SIDs extracted: {len(sids)}")
                return sids, total_lines
        print("That column doesn't appear to contain valid SIDs. Please try again.")

    while True:
        fname_col = prompt_column("Enter column number with SID-containing filenames (enter 0 if none): ")
        if fname_col == -1:
            print("No SIDs detected; exiting.")
            return set(), 0
        with open(path, newline='') as f:
            reader = csv.reader(f)
            if has_header:
                next(reader, None)
            if any(looks_like_valid_filename(row[fname_col].strip()) for row in reader if len(row) > fname_col):
                sids = set()
                total_lines = 0
                error_log = open("error.log", "a")
                with open(path, newline='') as f:
                    reader = csv.reader(f)
                    if has_header:
                        next(reader, None)
                    for row in reader:
                        total_lines += 1
                        try:
                            if len(row) <= fname_col:
                                raise ValueError("Row too short")
                            val = row[fname_col].strip()
                            sid = extract_sid_from_filename(val)
                            if not sid:
                                raise ValueError("No SID found in filename")
                            ext = os.path.splitext(val)[1].lower()
                            if ext not in VALID_IMAGE_EXTENSIONS:
                                raise ValueError(f"Invalid file extension: {ext}")
                            norm_sid = sid.lstrip("0")
                            sids.add(norm_sid)
                        except Exception as e:
                            error_log.write(f"{file_label} line {total_lines}: {e}\n")
                error_log.close()
                print(f"Total lines processed from {file_label}: {total_lines}")
                print(f"Unique valid SIDs extracted: {len(sids)}")
                return sids, total_lines
        print("That column doesn't appear to contain valid SID-containing filenames. Please try again.")

# -------- Main logic --------

def main():
    file1 = prompt_file("Enter path to first CSV file: ")
    sids1, total1 = extract_sids_from_csv(file1, "FILE1")
    if total1 == 0:
        sys.exit(1)

    file2 = prompt_file("Enter path to second CSV file: ")
    sids2, total2 = extract_sids_from_csv(file2, "FILE2")

    print("\n--- SID Comparison Summary ---")
    print(f"Total lines in {file1}: {total1}")
    print(f"Total lines in {file2}: {total2}")

    common = sids1 & sids2
    only1 = sids1 - sids2
    only2 = sids2 - sids1

    print(f"SIDs found in both files: {len(common)}")

    base1 = os.path.splitext(os.path.basename(file1))[0]
    base2 = os.path.splitext(os.path.basename(file2))[0]

    if prompt_yes_no("Do you want to write the shared SIDs to a CSV file?"):
        default_common = f"{base1}_{base2}_common.csv"
        out_common = prompt_output_filename(default_common)
        write_sid_list(common, out_common)

    if prompt_yes_no(f"Do you want to write SIDs unique to {file1}?"):
        default_unique1 = f"{base1}_unique.csv"
        out_unique1 = prompt_output_filename(default_unique1)
        write_sid_list(only1, out_unique1)

    if prompt_yes_no(f"Do you want to write SIDs unique to {file2}?"):
        default_unique2 = f"{base2}_unique.csv"
        out_unique2 = prompt_output_filename(default_unique2)
        write_sid_list(only2, out_unique2)

if __name__ == "__main__":
    main()


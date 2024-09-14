import os
import threading
import time
from pathlib import Path
from typing import Union
import keyboard
from inspyre_toolbox.path_man import provision_path
import re


def is_likely_filepath(input_str, strict_file_check=False):
    """
    Check if the input string is likely a file path.

    Parameters:
        input_str (str):
            The input string to check.

        strict_file_check (bool, optional):
            If True, the function will check for specific file-like patterns.
            Defaults to False.
    """

    # 1. Check for invalid path characters (generic for both files and directories)
    if any(char in ':*?"<>|' for char in input_str):
        return False

    # 2. Check for path-like structure: includes at least one path separator (/ or \)
    if not ("/" in input_str or "\\" in input_str):
        return False

    # 3. Normalize the path (cross-platform compatible)
    norm_path = os.path.normpath(input_str)

    # 4. If strict_file_check is True, check for specific file-like patterns
    if strict_file_check:
        # Ensure the path doesn't end with a slash/backslash (which usually indicates a directory)
        if re.match(r"[/\\]$", input_str):
            return False
        # Check if the path has a file extension
        _, ext = os.path.splitext(norm_path)
        if not ext:
            return False

    # 5. Check for any trailing slash or backslash, which may indicate a directory
    if re.match(r"[/\\]$", input_str):
        return True

    return True



def has_changed(file_path, last_modified_time):
    """
    Check if the file has been modified since the last time it was checked.

    Args:
        file_path (str):
            The path to the file to check.

        last_modified_time (float):
            The last time the file was checked.

    Returns:
        bool: True if the file has been modified, False if it has not.
    """
    try:
        current_modified_time = os.path.getmtime(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False

    if current_modified_time != last_modified_time and last_modified_time < current_modified_time:
        print(f"File has been modified at: {time.ctime(current_modified_time)}")
        return True
    else:
        print("No changes detected, continuing to monitor...")
        return False


def wait_for_changes(config_factory, interval=1):
    """
    Waits for changes to the file at the given path or until the user presses Enter.

    Args:
        config_factory (ConfigFactory):
            The ConfigFactory object that contains the file path to monitor.

        interval (Union[int, float]):
            The interval in seconds to check for changes.

    Returns:
        bool: True if the file was modified, False if the user pressed Enter without modification.
    """
    cf = config_factory
    file_path = cf.config_file_path
    if isinstance(file_path, str):
        file_path = Path(file_path).expanduser().resolve().absolute()

    interval = float(interval)

    try:
        last_modified_time = os.path.getmtime(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False

    fp_str = str(file_path)

    # Open the file in the default editor
    os.startfile(fp_str)

    modification_detected = threading.Event()
    enter_pressed = threading.Event()

    def check_modifications():
        nonlocal last_modified_time
        while not modification_detected.is_set() and not enter_pressed.is_set():
            if enter_pressed.is_set():
                break
            try:
                current_modified_time = os.path.getmtime(file_path)
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                return
            if current_modified_time != last_modified_time:
                print(f"File has been modified at: {time.ctime(current_modified_time)}")
                config_factory._ConfigFactory__file_modified = True
                modification_detected.set()
            else:
                time.sleep(interval)
                print("No changes detected, continuing to monitor...")

    def on_press(event):
        if keyboard.is_pressed('enter') and keyboard.is_pressed('esc'):
            print("Enter and ESC keys pressed.")
            enter_pressed.set()
            keyboard.unhook_all()  # Unhook all the keyboard hooks
            return False  # Stop the listener

    checker_thread = threading.Thread(target=check_modifications)
    checker_thread.start()

    keyboard.on_press(on_press)

    # Join the threads but only if neither event is set yet
    while not modification_detected.is_set() and not enter_pressed.is_set():
        time.sleep(0.1)

    # Ensure the checker thread is joined before exiting
    checker_thread.join()

    print("Exiting wait_for_changes...")


    return config_factory._ConfigFactory__file_modified

def conjugate(lst, conjunction='and'):
    if conjunction not in ['and', 'or']:
        raise ValueError("Conjunction must be 'and' or 'or'.")

    if not lst:
        return ""
    elif len(lst) == 1:
        return lst[0]
    elif len(lst) == 2:
        return f"{lst[0]} {conjunction} {lst[1]}"
    else:
        return ", ".join(lst[:-1]) + f", {conjunction} " + lst[-1]


def search_file_for_user_line(file_path):
    """
    Search the file for the line containing the user's name.

    Args:
        file_path (str):
            The path to the file to search.

    Returns:
        str: The line containing the user's name.
    """
    from warnings import warn
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if '[USER]' in line:
                    return line.strip()
        return None
    except FileNotFoundError:
        warn(f'File not found: {file_path}')
    except Exception as e:
        warn(f'Error reading file: {file_path}\n{e}')
        return None


def get_provisioned_path_str(path: Union[str, Path]) -> str:
    """
    Get the string representation of the provisioned path.

    Args:
        path (Union[str, Path]):
            The path to convert.

    Returns:
        str: The string representation of the path.
    """
    return str(provision_path(path))

import os
import re
import sys
from rapidfuzz import process, fuzz  # Import rapidfuzz for fuzzy matching

from colorama import Fore, init, Style


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""

    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            try:
                self.impl = _GetchUnix()
            except AttributeError:
                self.impl = _GetchUnix()

    def __call__(self):
        return self.impl()


class _GetchUnix:
    def __init__(self):
        self = self

    def __call__(self):
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()


def menu(menutitle, options, printhelp=True, autoselect=False, fuzzy=False):
    """
    Generate a terminal fuzzy menu with regex-based searching, fuzzy searching, and autoselect.

    @param string       menutitle
    @param list strings options
    @param boolean      printhelp (default=True)
    @param boolean      autoselect (default=False)
    @param boolean      fuzzy (default=False, press [TAB] to swith between regex and fuzzy search)

    @return string      selected option by user
    """

    init()
    keyboardinput = ""
    selected = 0  # Start with the first option selected
    while True:
        # Clear terminal
        os.system('cls' if os.name == 'nt' else 'clear')

        # Generate current selection menu filtered with user input
        current = [content.replace("\n", "") for content in options]
        matches = []

        if keyboardinput.strip():
            if fuzzy:
                # Use fuzzy matching to filter options
                matches = process.extract(
                    keyboardinput, current, scorer=fuzz.partial_ratio, limit=10
                )
                # Keep only matches with a score above a threshold (e.g., 60)
                current = [match[0] for match in matches if match[1] > 60]
            else:
                # Use regex to filter options if the input is a valid regex
                try:
                    regex = re.compile(keyboardinput, re.IGNORECASE)
                    current = [content for content in current if regex.search(content)]
                except re.error:
                    # If the regex is invalid, show all options
                    pass

        # Autoselect if only one option is left
        if autoselect and len(current) == 1:
            print(f"Automatically selected: {current[0]}")
            return current[0]

        # Ensure the selected index is within bounds
        selected = max(0, min(selected, len(current) - 1))

        # Print the menu with the current selected entry highlighted
        for i, item in enumerate(current):
            if fuzzy:
                # Highlight the matched part for fuzzy search
                match = next((m for m in matches if m[0] == item), None)
                if match:
                    start = item.lower().find(keyboardinput.lower())
                    if start != -1:
                        end = start + len(keyboardinput)
                        highlighted = (
                            item[:start]
                            + Fore.YELLOW
                            + item[start:end]
                            + Style.RESET_ALL
                            + item[end:]
                        )
                    else:
                        highlighted = item
                else:
                    highlighted = item
            else:
                # Highlight the matched part for regex search
                try:
                    regex = re.compile(keyboardinput, re.IGNORECASE)
                    highlighted = regex.sub(
                        lambda m: f"{Fore.YELLOW}{m.group(0)}{Style.RESET_ALL}", item
                    )
                except re.error:
                    highlighted = item

            if i == selected:
                print(f" {Fore.RED}>>{Style.RESET_ALL} {highlighted}")  # Highlight the selected item
            else:
                print(f"    {highlighted}")

        # Print the write section
        if printhelp:
            print(
                "Default hotkeys: [enter] select, [up/down arrows] navigate, [esc] clean, [Ctrl+c] exit\n"
                "You can also type a valid regex or fuzzy input to filter the options.\n"
            )
        print(menutitle + "~$ " + keyboardinput + "|")
        print(f"Fuzzy search: {fuzzy}")

        # Read user input
        stdin = getch()
        if sys.platform == "win32":
            stdin = stdin.decode("utf-8", "replace")

        # Handle multi-character escape sequences for arrow keys
        if stdin == "\x1b":  # Escape sequence
            next_char = getch()
            if next_char == "[":
                arrow_key = getch()
                if arrow_key == "A":  # Up arrow
                    selected -= 1
                elif arrow_key == "B":  # Down arrow
                    selected += 1
            continue

        # Validate input
        if stdin == "\r":  # Enter
            if len(current) > 0:
                return current[selected]
        elif stdin == "\x1b":  # Esc
            keyboardinput = ""
            selected = 0
        elif stdin == "\x7f" or stdin == "\x08":  # Backspace
            keyboardinput = keyboardinput[:-1]
        elif stdin == "\x20":  # Space
            keyboardinput += " "
        elif stdin == "\x03":  # Ctrl+C
            quit()
        elif stdin == "\t":  # Tab
            fuzzy = not fuzzy
        elif re.fullmatch(r"[^\x00-\x1F\x7F]", stdin):  # Match printable characters
            keyboardinput += stdin
            selected = 0


# Define the menu title and options
menu_title = "Main Menu"
menu_options = [
    "add item",
    "remove item",
    "clear all",
    "exit",
    "test 1",
    "volba zde",
    "test 5",
    "test 6",
    "test 7",
]

# Call the menu function
selected_option = menu(menu_title, menu_options, autoselect=False, fuzzy=False)

# Print the selected option
print(f"Selected option: {selected_option}")
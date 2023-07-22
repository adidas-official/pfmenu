import os
import re
import sys


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""

    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            try:
                self.impl = _GetchMacCarbon()
            except ImportError:
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


class _GetchMacCarbon:
    """
    A function which returns the current ASCII key that is down;
    if no ASCII key is down, the null string is returned.  The
    page http://www.mactech.com/macintosh-c/chap02-1.html was
    very helpful in figuring out how to do this.
    """

    def __init__(self):
        import Carbon
        Carbon.Evt  # see if it has this (in Unix, it doesn't)

    def __call__(self):
        import Carbon
        if Carbon.Evt.EventAvail(0x0008)[0] == 0:  # 0x0008 is the keyDownMask
            return ''
        else:
            #
            # The event contains the following info:
            # (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            #
            # The message (msg) contains the ASCII char which is
            # extracted with the 0x000000FF charCodeMask; this
            # number is converted to an ASCII character with chr() and
            # returned
            #
            (what, msg, when, where, mod) = Carbon.Evt.GetNextEvent(0x0008)[1]
            return chr(msg & 0x000000FF)


getch = _Getch()


def menu(menutitle, options, printhelp=True):
    """
    generate a terminal fuzzy menu

    @param string       menutitle
    @param list strings options
    @param boolean      printhelp (default=True)

    @return string      selected option by user
    """

    pat = re.compile(r"[A-Za-z0-9]+|:|\.|-|_|/|\\|\[|\]|~")

    keyboardinput = ""
    selected = -1
    while True:

        # clear terminal
        os.system('cls' if os.name == 'nt' else 'clear')

        # generate current selection menu filtered with user input
        current = [content.replace("\n", "") for content in options]
        for filter in keyboardinput.split():
            current = [content.replace(
                "\n", "") for content in current if filter.lower() in content.lower()]
        if keyboardinput == "":
            current.append("")

        # print in menu the current selected entry
        selected *= (selected < len(current))
        if len(current) != 0:
            current[selected] = " >> " + current[selected]

        # print menu
        print("\n".join(current))

        # print write section
        if printhelp:
            print(
                "Default hotkeys: [enter] select, [tab] select between current selection, [esc] clean, [Ctrl+c] exit\n")
        print(menutitle + "~$ " + keyboardinput + "|")

        stdin = getch()
        if b"\xe0" == stdin:  # skip escape sequences
            continue
        if sys.platform == "win32":
            stdin = stdin.decode("utf-8", "replace")

        # validate input
        if "\r" == stdin:  # enter
            if len(current) > 0:
                if keyboardinput != current[selected].replace(" >> ", ""):
                    keyboardinput = current[selected].replace(
                        " >> ", "").replace("[args]", "")
                else:
                    return keyboardinput
            else:
                return keyboardinput
        if "\x1b" == stdin:  # esc
            keyboardinput = ""
            selected = -1
        if "\t" == stdin:  # tab
            selected += 1
        if "\x7f" == stdin or "\x08" == stdin:  # backspace
            keyboardinput = keyboardinput[:-1]
        if "\x20" == stdin:  # space
            keyboardinput += " "
        if "\x03" == stdin:  # C-c
            quit()
        if re.fullmatch(pat, stdin):
            keyboardinput += stdin
            selected = -1

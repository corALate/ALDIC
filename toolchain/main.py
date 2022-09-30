#!/usr/bin/env python3

import os
import signal
import getpass
import platform
import itertools

from mfc.util.common  import MFC_LOGO, MFCException, quit, delete_directory, format_list_to_string, does_command_exist
from mfc.util.printer import cons

from mfc     import args
from mfc     import build
from mfc.cfg import user
from mfc.cfg import lock

from mfc.run   import run
from mfc.tests import tests


class MFCState:
    def __init__(self) -> None:
        self.user = user.MFCUser()
        self.lock = lock.MFCLock(self.user)
        self.test = tests.MFCTest(self)
        self.args = args.parse(self)
        self.run  = run.MFCRun(self)

        self.__handle_mode()
        self.__print_greeting()
        self.__checks()
        self.__run()


    def __handle_mode(self):
        # Handle mode change
        if self.args["mode"] != self.lock.mode:
            cons.print(f"[bold yellow]Switching to [bold magenta]{self.args['mode']}[/bold magenta] mode from [bold magenta]{self.lock.mode}[/bold magenta] mode:[/bold yellow]")
            self.lock.mode = self.args["mode"]
            self.lock.write()

            for target_name in build.get_mfc_target_names():
                t = build.get_target(target_name)
                dirpath = build.get_build_dirpath(t)
                cons.print(f"[bold red] - Removing {os.path.relpath(dirpath)}[/bold red]")
                delete_directory(dirpath)


    def __print_greeting(self):
        MFC_LOGO_LINES       = MFC_LOGO.splitlines()
        max_logo_line_length = max([ len(line) for line in MFC_LOGO_LINES ])

        host_line = f"{getpass.getuser()}@{platform.node()} [{platform.system()}]"

        targets_line = \
            f"[bold]--targets: {format_list_to_string([ f'[magenta]{target}[/magenta]' for target in self.args['targets']], 'None')}[/bold]"

        MFC_SIDEBAR_LINES = [
            "",
            f"[bold]{host_line}[/bold]",
            '-' * len(host_line),
            "",
            "",
            f"[bold]--jobs:    [magenta]{self.args['jobs']}[/magenta][/bold]",
            f"[bold]--mode:    [magenta]{self.lock.mode}[/magenta][/bold]",
            targets_line if self.args["command"] != "test" else "",
            "",
            "",
            "[yellow]$ ./mfc.sh \[build, run, test, clean] --help[/yellow]",
        ]


        for a, b in itertools.zip_longest(MFC_LOGO_LINES, MFC_SIDEBAR_LINES):
            lhs = a.ljust(max_logo_line_length)
            rhs = b if b is not None else ''
            cons.print(
                f"[bold blue] {lhs} [/bold blue]  {rhs}",
                highlight=False
            )

        cons.print()


    def __checks(self):
        if not does_command_exist("cmake"):
            raise MFCException("CMake is required to build MFC but couldn't be located on your system. Please ensure it installed and discoverable (e.g in your system's $PATH).")

        if not does_command_exist("mpif90") and not self.args["no_mpi"]:
            raise MFCException("mpif90 couldn't be located on your system. We therefore assume MPI is not available on your system. It is required to build MFC. Please ensure it is installed and discoverable (e.g in your system's $PATH).")


    def __run(self):
        if self.args["command"] == "test":
            self.test.execute()
        elif self.args["command"] == "run":
            self.run.run()
        elif self.args["command"] == "build":
            build.build(self)
        elif self.args["command"] == "clean":
            for target in self.args["targets"]:
                build.clean_target(self, target)


if __name__ == "__main__":
    try:
        MFCState()
    except MFCException as exc:
        cons.reset()
        cons.print(f"""\


[bold red]Error[/bold red]: {str(exc)}
""")
        quit(signal.SIGTERM)
    except KeyboardInterrupt as exc:
        quit(signal.SIGTERM)
    except Exception as exc:
        cons.reset()
        cons.print_exception()
        cons.print(f"""\


[bold red]ERROR[/bold red]: An unexpected exception occurred: {str(exc)}
""")

        quit(signal.SIGTERM)

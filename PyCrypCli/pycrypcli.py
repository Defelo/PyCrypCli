import getpass
import os
import sys
from os import getenv
from typing import List, Optional, Tuple

import sentry_sdk

from PyCrypCli.commands.command import make_commands, COMMAND_FUNCTION, command
from PyCrypCli.context import Context, LoginContext, MainContext, RootContext, DeviceContext, COMPLETER_FUNCTION
from PyCrypCli.exceptions import *

try:
    import readline
except ImportError:
    import pyreadline as readline

if not getenv("DEBUG"):
    sentry_sdk.init(
        dsn="https://dbfe81c972c84a77a30d915cbfb538c7@o380163.ingest.sentry.io/5226857",
        attach_stacktrace=True,
        shutdown_timeout=5,
    )


class Frontend:
    def __init__(self, server: str, config_file: List[str]):
        self.config_file: List[str] = config_file

        self.history: List[str] = []

        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        readline.set_completer_delims(" ")

        self.root_context: RootContext = RootContext(server, config_file, make_commands())
        self.root_context.open(LoginContext(self.root_context))

    def complete_command(self, text: str) -> List[str]:
        override_completions: Optional[List[str]] = self.root_context.get_override_completions()
        if override_completions is not None:
            return override_completions

        cmd, *args = text.split(" ") or [""]
        if not args:
            return [cmd for cmd in self.root_context.get_commands()]
        else:
            completer: Optional[COMPLETER_FUNCTION] = self.root_context.get_commands().get(cmd, (None, None, None))[2]
            if completer is not None:
                return completer(self.get_context(), args) or []
            else:
                return []

    def completer(self, text: str, state: int) -> Optional[str]:
        readline.set_completer_delims(" ")
        options: List[str] = self.complete_command(readline.get_line_buffer())
        options: List[str] = [o + " " if o[-1:] != "\0" else o[:-1] for o in sorted(options) if o.startswith(text)]

        if state < len(options):
            return options[state]
        return None

    def get_context(self) -> Context:
        return self.root_context.get_context()

    @staticmethod
    @command(["register", "signup"], [LoginContext], "Create a new account")
    def register(context: LoginContext, *_):
        try:
            username: str = context.input_no_history("Username: ")
            mail: str = context.input_no_history("Email Address: ")
            password: str = getpass.getpass("Password: ")
            confirm_password: str = getpass.getpass("Confirm Password: ")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return

        if password != confirm_password:
            print("Passwords don't match.")
            return
        try:
            session_token: str = context.get_client().register(username, mail, password)
            context.open(MainContext(context.root_context, session_token))
        except WeakPasswordException:
            print("Password is too weak.")
            return
        except UsernameAlreadyExistsException:
            print("Username already exists.")
            return
        except InvalidEmailException:
            print("Invalid email")
            return

    @staticmethod
    @command(["login"], [LoginContext], "Login with an existing account")
    def login(context: LoginContext, *_):
        try:
            username: str = context.input_no_history("Username: ")
            password: str = getpass.getpass("Password: ")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return

        try:
            session_token: str = context.get_client().login(username, password)
            context.open(MainContext(context.root_context, session_token))
        except InvalidLoginException:
            print("Invalid Login Credentials.")
            return

    @staticmethod
    @command(["exit", "quit"], [LoginContext], "Exit PyCrypCli")
    def handle_main_exit(*_):
        exit()

    @staticmethod
    @command(["exit", "quit"], [MainContext], "Exit PyCrypCli (session will be saved)")
    def handle_main_exit(context: MainContext, *_):
        context.get_client().close()
        exit()

    @staticmethod
    @command(["exit", "quit", "logout"], [DeviceContext], "Disconnect from this device")
    def handle_main_exit(context: DeviceContext, *_):
        context.close()

    @staticmethod
    @command(["logout"], [MainContext], "Delete the current session and exit PyCrypCli")
    def handle_main_logout(context: MainContext, *_):
        context.close()

    @staticmethod
    @command(["passwd"], [MainContext], "Change your password")
    def handle_passwd(context: MainContext, *_):
        old_password: str = getpass.getpass("Current password: ")
        new_password: str = getpass.getpass("New password: ")
        confirm_password: str = getpass.getpass("Confirm password: ")

        if new_password != confirm_password:
            print("Passwords don't match.")
            return

        context.get_client().close()
        try:
            context.get_client().change_password(context.username, old_password, new_password)
            print("Password updated successfully.")
        except PermissionsDeniedException:
            print("Incorrect password or the new password does not meet the requirements.")
        context.get_client().session(context.session_token)

    @staticmethod
    @command(["_delete_user"], [MainContext], "Delete this account")
    def handle_delete_user(context: MainContext, *_):
        if context.ask("Are you sure you want to delete your account? [yes|no] ", ["yes", "no"]) == "no":
            print("Your account has NOT been deleted.")
            return

        print("Warning! This action cannot be undone!")
        print("Are you absolutely sure you want to delete this account?")
        try:
            if context.input_no_history("Type in the name of this account to confirm: ") == context.username:
                context.get_client().delete_user()
                print(f"The account '{context.username}' has been deleted successfully.")
                context.close()
            else:
                print("Your account has NOT been deleted.")
        except (KeyboardInterrupt, EOFError):
            print("\nYour account has NOT been deleted.")

    @staticmethod
    @command(["help"], [LoginContext, MainContext, DeviceContext], "Show a list of available commands")
    def handle_main_help(context: Context, *_):
        commands: List[Tuple[str, str]] = ([(c, d) for c, (d, *_) in context.get_commands().items()])
        print("Available commands:")
        max_length: int = max(len(cmd[0]) for cmd in commands)
        for com, desc in commands:
            com: str = com.ljust(max_length)
            print(f" - {com}    {desc}")

    @staticmethod
    @command(["clear"], [LoginContext, MainContext, DeviceContext], "Clear the console")
    def handle_main_clear(*_):
        print(end="\033c")

    @staticmethod
    @command(["history"], [MainContext, DeviceContext], "Show the history of commands entered in this session")
    def handle_main_history(context: MainContext, *_):
        for line in context.history:
            print(line)

    @staticmethod
    @command(["feedback"], [LoginContext, MainContext, DeviceContext], "Send feedback to the developer")
    def feedback(context: Context, *_):
        print("Please type your feedback about PyCrypCli below. When you are done press Ctrl+C")
        feedback = ["User Feedback"]
        if hasattr(context, "username"):
            feedback[0] += " from " + context.username
        while True:
            try:
                feedback.append(input("> "))
            except (KeyboardInterrupt, EOFError):
                break
        print()
        print("=" * 30)
        print("\n".join(feedback))
        print("=" * 30)
        if context.ask("Do you want to send this feedback to the developer? [yes|no] ", ["yes", "no"]) == "yes":
            sentry_sdk.capture_message("\n".join(feedback))

    def mainloop(self):
        while True:
            self.get_context().loop_tick()
            context: Context = self.get_context()

            prompt: str = context.get_prompt()
            try:
                cmd, *args = input(prompt).strip().split(" ")
                if not cmd:
                    continue
            except EOFError:  # Ctrl-D
                print("exit")
                cmd, args = "exit", []
            except KeyboardInterrupt:  # Ctrl-C
                print("^C")
                continue

            if not context.before_command():
                continue

            context.add_to_history(cmd + " " + " ".join(args))

            if cmd in context.get_commands():
                func: COMMAND_FUNCTION = context.get_commands()[cmd][1]
                func(context, args)
            else:
                print("Command could not be found.")
                print("Type `help` for a list of commands.")


def main():
    print(
        "\033[32m\033[1m"
        + r"""
       ______                 __  _     
      / ____/______  ______  / /_(_)____
     / /   / ___/ / / / __ \/ __/ / ___/
    / /___/ /  / /_/ / /_/ / /_/ / /__  
    \____/_/   \__, / .___/\__/_/\___/  
              /____/_/                  
"""
        + "\033[0m"
    )
    print("Python Cryptic Game Client (https://github.com/Defelo/PyCrypCli)")
    print("You can always type `help` for a list of available commands.")

    server: str = "wss://ws.cryptic-game.net/"
    if len(sys.argv) > 1:
        server: str = sys.argv[1]
        if server.lower() == "test":
            server: str = "wss://ws.test.cryptic-game.net/"
        elif not server.startswith("wss://") and not server.startswith("ws://"):
            server: str = "ws://" + server

    frontend: Frontend = Frontend(server, [os.path.expanduser("~"), ".config", "PyCrypCli", "config.json"])
    frontend.mainloop()


if __name__ == "__main__":
    main()

import getpass
import sys
from typing import Any

from .command import command, CommandError
from ..context import LoginContext, MainContext, DeviceContext
from ..exceptions import WeakPasswordError, UsernameAlreadyExistsError, InvalidLoginError, PermissionDeniedError


@command("register", [LoginContext], aliases=["signup"])
def register(context: LoginContext, _: Any) -> None:
    """
    Create a new account
    """

    try:
        username: str = context.input_no_history("Username: ")
        password: str = getpass.getpass("Password: ")
        confirm_password: str = getpass.getpass("Confirm Password: ")
    except (KeyboardInterrupt, EOFError):
        raise CommandError("\nAborted.")

    if password != confirm_password:
        raise CommandError("Passwords don't match.")
    try:
        session_token: str = context.client.register(username, password).token
        context.open(MainContext(context.root_context, session_token))
    except WeakPasswordError:
        raise CommandError("Password is too weak.")
    except UsernameAlreadyExistsError:
        raise CommandError("Username already exists.")


@command("login", [LoginContext])
def login(context: LoginContext, _: Any) -> None:
    """
    Login with an existing account
    """

    try:
        username: str = context.input_no_history("Username: ")
        password: str = getpass.getpass("Password: ")
    except (KeyboardInterrupt, EOFError):
        raise CommandError("\nAborted.")

    try:
        session_token: str = context.client.login(username, password).token
        context.open(MainContext(context.root_context, session_token))
    except InvalidLoginError:
        raise CommandError("Invalid Login Credentials.")


@command("exit", [LoginContext], aliases=["quit"])
def handle_login_exit(*_: Any) -> None:
    """
    Exit PyCrypCli
    """

    sys.exit()


@command("exit", [MainContext], aliases=["quit"])
def handle_main_exit(context: MainContext, _: Any) -> None:
    """
    Exit PyCrypCli (session will be saved)
    """

    context.client.close()
    sys.exit()


@command("exit", [DeviceContext], aliases=["quit", "logout"])
def handle_device_exit(context: DeviceContext, _: Any) -> None:
    """
    Disconnect from this device
    """

    context.close()


@command("logout", [MainContext])
def handle_main_logout(context: MainContext, _: Any) -> None:
    """
    Delete the current session and exit PyCrypCli
    """

    context.close()


@command("passwd", [MainContext])
def handle_passwd(context: MainContext, _: Any) -> None:
    """
    Change your password
    """

    old_password: str = getpass.getpass("Current password: ")
    new_password: str = getpass.getpass("New password: ")
    confirm_password: str = getpass.getpass("Confirm password: ")

    if new_password != confirm_password:
        raise CommandError("Passwords don't match.")

    try:
        context.session_token = context.client.change_password(old_password, new_password).token
        context.save_session()
        print("Password updated successfully.")
    except PermissionDeniedError:
        raise CommandError("Incorrect password or the new password does not meet the requirements.")


@command("_delete_user", [MainContext])
def handle_delete_user(context: MainContext, _: Any) -> None:
    """
    Delete this account
    """

    if context.ask("Are you sure you want to delete your account? [yes|no] ", ["yes", "no"]) == "no":
        raise CommandError("Your account has NOT been deleted.")

    print("Warning! This action cannot be undone!")
    print("Are you absolutely sure you want to delete this account?")
    try:
        if context.input_no_history("Type in the name of this account to confirm: ") == context.username:
            context.client.delete_user()
            print(f"The account '{context.username}' has been deleted successfully.")
            context.close()
        else:
            raise CommandError("Your account has NOT been deleted.")
    except (KeyboardInterrupt, EOFError):
        raise CommandError("\nYour account has NOT been deleted.")

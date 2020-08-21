import getpass
import sys

from PyCrypCli.commands import command, CommandError
from PyCrypCli.context import LoginContext, MainContext, DeviceContext
from PyCrypCli.exceptions import (
    WeakPasswordException,
    UsernameAlreadyExistsException,
    InvalidLoginException,
    PermissionsDeniedException,
)


@command("register", [LoginContext], aliases=["signup"])
def register(context: LoginContext, *_):
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
        session_token: str = context.client.register(username, password)
        context.open(MainContext(context.root_context, session_token))
    except WeakPasswordException:
        raise CommandError("Password is too weak.")
    except UsernameAlreadyExistsException:
        raise CommandError("Username already exists.")


@command("login", [LoginContext])
def login(context: LoginContext, *_):
    """
    Login with an existing account
    """

    try:
        username: str = context.input_no_history("Username: ")
        password: str = getpass.getpass("Password: ")
    except (KeyboardInterrupt, EOFError):
        raise CommandError("\nAborted.")

    try:
        session_token: str = context.client.login(username, password)
        context.open(MainContext(context.root_context, session_token))
    except InvalidLoginException:
        raise CommandError("Invalid Login Credentials.")


@command("exit", [LoginContext], aliases=["quit"])
def handle_login_exit(*_):
    """
    Exit PyCrypCli
    """

    sys.exit()


@command("exit", [MainContext], aliases=["quit"])
def handle_main_exit(context: MainContext, *_):
    """
    Exit PyCrypCli (session will be saved)
    """

    context.client.close()
    sys.exit()


@command("exit", [DeviceContext], aliases=["quit", "logout"])
def handle_device_exit(context: DeviceContext, *_):
    """
    Disconnect from this device
    """

    context.close()


@command("logout", [MainContext])
def handle_main_logout(context: MainContext, *_):
    """
    Delete the current session and exit PyCrypCli
    """

    context.close()


@command("passwd", [MainContext])
def handle_passwd(context: MainContext, *_):
    """
    Change your password
    """

    old_password: str = getpass.getpass("Current password: ")
    new_password: str = getpass.getpass("New password: ")
    confirm_password: str = getpass.getpass("Confirm password: ")

    if new_password != confirm_password:
        raise CommandError("Passwords don't match.")

    context.client.close()
    try:
        context.client.change_password(context.username, old_password, new_password)
        print("Password updated successfully.")
    except PermissionsDeniedException:
        raise CommandError("Incorrect password or the new password does not meet the requirements.")
    finally:
        context.client.session(context.session_token)


@command("_delete_user", [MainContext])
def handle_delete_user(context: MainContext, *_):
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

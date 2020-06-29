import getpass

from PyCrypCli.commands import command
from PyCrypCli.context import LoginContext, MainContext, DeviceContext
from PyCrypCli.exceptions import (
    WeakPasswordException,
    UsernameAlreadyExistsException,
    InvalidEmailException,
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


@command("login", [LoginContext])
def login(context: LoginContext, *_):
    """
    Login with an existing account
    """

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


@command("exit", [LoginContext], aliases=["quit"])
def handle_main_exit(*_):
    """
    Exit PyCrypCli
    """

    exit()


@command("exit", [MainContext], aliases=["quit"])
def handle_main_exit(context: MainContext, *_):
    """
    Exit PyCrypCli (session will be saved)
    """

    context.get_client().close()
    exit()


@command("exit", [DeviceContext], aliases=["quit", "logout"])
def handle_main_exit(context: DeviceContext, *_):
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
        print("Passwords don't match.")
        return

    context.get_client().close()
    try:
        context.get_client().change_password(context.username, old_password, new_password)
        print("Password updated successfully.")
    except PermissionsDeniedException:
        print("Incorrect password or the new password does not meet the requirements.")
    context.get_client().session(context.session_token)


@command("_delete_user", [MainContext])
def handle_delete_user(context: MainContext, *_):
    """
    Delete this account
    """

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

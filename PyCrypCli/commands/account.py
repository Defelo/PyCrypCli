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


@command("register", [LoginContext], "Create a new account", aliases=["signup"])
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


@command("login", [LoginContext], "Login with an existing account")
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


@command("exit", [LoginContext], "Exit PyCrypCli", aliases=["quit"])
def handle_main_exit(*_):
    exit()


@command("exit", [MainContext], "Exit PyCrypCli (session will be saved)", aliases=["quit"])
def handle_main_exit(context: MainContext, *_):
    context.get_client().close()
    exit()


@command("exit", [DeviceContext], "Disconnect from this device", aliases=["quit", "logout"])
def handle_main_exit(context: DeviceContext, *_):
    context.close()


@command("logout", [MainContext], "Delete the current session and exit PyCrypCli")
def handle_main_logout(context: MainContext, *_):
    context.close()


@command("passwd", [MainContext], "Change your password")
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


@command("_delete_user", [MainContext], "Delete this account")
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

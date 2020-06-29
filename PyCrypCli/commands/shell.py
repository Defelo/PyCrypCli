import sentry_sdk

from PyCrypCli.commands import command
from PyCrypCli.context import LoginContext, MainContext, DeviceContext, Context


@command("clear", [LoginContext, MainContext, DeviceContext])
def handle_main_clear(*_):
    """
    Clear the console
    """

    print(end="\033c")


@command("history", [MainContext, DeviceContext])
def handle_main_history(context: MainContext, *_):
    """
    Show the history of commands entered in this session
    """

    for line in context.history:
        print(line)


@command("feedback", [LoginContext, MainContext, DeviceContext])
def handle_feedback(context: Context, *_):
    """
    Send feedback to the developer
    """

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

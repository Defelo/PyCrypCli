from typing import Any

import sentry_sdk

from .command import command
from ..context import LoginContext, MainContext, DeviceContext


@command("clear", [LoginContext, MainContext, DeviceContext])
def handle_main_clear(*_: Any) -> None:
    """
    Clear the console
    """

    print(end="\033c")


@command("history", [MainContext, DeviceContext])
def handle_main_history(context: MainContext, _: Any) -> None:
    """
    Show the history of commands entered in this session
    """

    for line in context.history:
        print(line)


@command("feedback", [LoginContext, MainContext, DeviceContext])
def handle_feedback(context: LoginContext, _: Any) -> None:
    """
    Send feedback to the developer
    """

    print("Please type your feedback about PyCrypCli below. When you are done press Ctrl+C")
    feedback = ["User Feedback"]
    if isinstance(context, MainContext) and context.username:
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

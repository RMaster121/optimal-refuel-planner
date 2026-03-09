#!/usr/bin/env python
import os
import sys

# import pydevd_pycharm

def main():
    """Run administrative tasks."""

    # Connect to the PyCharm debug server
    # pydevd_pycharm.settrace('host.docker.internal', port=5789, stdoutToServer=True, stderrToServer=True, suspend=False)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "refuel_planner.settings")
    try:
        from django.core.management import execute_from_command_line  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
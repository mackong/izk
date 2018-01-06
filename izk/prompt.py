import argparse
import traceback

from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from pygments.styles.monokai import MonokaiStyle

from .runner import ZkCommandRunner, command_usage
from .lexer import ZkCliLexer
from .zk import ExtendedKazooClient
from .completion import ZkCompleter
from .validation import UnknownCommand, CommandValidationError


history = InMemoryHistory()
auto_suggest = AutoSuggestFromHistory()


def parse_args():
    parser = argparse.ArgumentParser(
        description='CLI for zookeeper with syntax-highlighting and auto-completion')
    parser.add_argument('zk_url', help='URL of the zookeeper node')
    return parser.parse_args()


def print_headers(zkcli):
    print(zkcli.command(b'srvr'))


def main():
    cmd_index = 0
    args = parse_args()

    with ExtendedKazooClient(hosts=args.zk_url, timeout=2) as zkcli:
        print_headers(zkcli)
        cmdrunner = ZkCommandRunner(zkcli)
        while True:
            # We need a new completer for each command
            completer = ZkCompleter(zkcli)
            try:
                cmd = prompt(
                    '(%d) > ' % (cmd_index),
                    history=history,
                    auto_suggest=auto_suggest,
                    completer=completer,
                    lexer=ZkCliLexer,
                    style=MonokaiStyle)
                try:
                    out = cmdrunner.run(cmd)
                except CommandValidationError as exc:
                    # The command was invalid. Print command help and usage.
                    print(exc, end='\n\n')
                    print(command_usage(exc.command))
                except (NoNodeError, UnknownCommand) as exc:
                    print(exc)
                else:
                    if out is not None:
                        print(out)
            except (KeyboardInterrupt, EOFError) as exc:
                break
            except Exception:
                traceback.print_exc()
            finally:
                cmd_index += 1


if __name__ == '__main__':
    main()

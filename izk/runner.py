import re
import datetime

from .lexer import KEYWORDS
from .formatting import colorize

# A zookeeper CLI command
COMMAND = r'(%s)' % ('|'.join(KEYWORDS))

# A znode path
PATH = r'/[^\s]*'

# A string-value, without the quotes
STR = r"((?<=')[^']+(?=')|(?<=\")[^\"]+(?=\"))"
from .validation import validate_command_input

# A CLI user-input token can either be a command, a path or a string
TOKEN = r'(%s)' % '|'.join([COMMAND, PATH, STR])


def command_usage(command_name):
    """Print the usage of the argument command."""
    doc = getattr(ZkCommandRunner, command_name).__doc__
    lines = doc.split('\n')[1:]  # remove first line
    lines = [line.strip() for line in lines]
    return '\n'.join(lines).strip()


def command_help(command_name, short=False):
    """Display the help (short or not) of the argument command."""
    command = getattr(ZkCommandRunner, command_name, None)
    if not command:
        return ''
    doc = command.__doc__
    if not doc:
        return ''
    lines = doc.split('\n')
    lines = [line.strip() for line in lines]
    if short:
        lines = [lines[0]]
    return '\n'.join(lines).strip()


def commands_help():
    """Display the short help of all available commands."""
    _help = ['Commands:']
    for command_name in KEYWORDS:
        command_short_help = command_help(command_name, short=True)
        _help.append('- %s: %s' % (command_name, command_short_help))
    return '\n'.join(_help)


class ZkCommandRunner:
    """Object in charge of running the zookeeper commands."""

    def __init__(self, zkcli):
        self.zkcli = zkcli

    def _tokenize(self, command_str):
        tokens = re.findall(TOKEN, command_str)
        return [tok[0] for tok in tokens]

    def close(self):
        """Close the shell"""
        raise KeyboardInterrupt

    def quit(self):
        """Close the shell"""
        raise KeyboardInterrupt

    def help(self, command_name=None):
        """Print the help of a command

        Usage: help [command]
        Examples:
        - help     # shows the list of commands
        - help ls  # show a command help

        """
        if command_name:
            return command_help(command_name)
        else:
            return commands_help()

    def ls(self, path):
        """Display the children of a ZNode

        Usage: ls <path>
        Example: ls /test

        """
        nodes = self.zkcli.get_children(path)
        return ' '.join(nodes)

    @colorize
    def get(self, path):
        """Display the content of a ZNode

        Usage: get <path>
        Example: get /test

        """
        node_data = self.zkcli.get_node(path)
        if node_data is None:
            raise Exception('%s does not exist' % (path))
        else:
            return node_data

    def create(self, path):
        """Recursively create a path if it doesn't exist

        Usage: create <path>
        Example: create /a/b/c/d

        """
        return self.zkcli.ensure_path(path)

    def set(self, path, data):
        """Set or update the content of a ZNode

        Usage: set <path> <data>
        Example: set /test '{"key": "value"}'

        """
        if not self.zkcli.exists(path):
            return self.zkcli.create(path, data.encode('utf-8'))
        else:
            self.zkcli.set(path, data.encode('utf-8'))

    def delete(self, path):
        """Delete a leaf ZNode

        Usage: delete <path>
        Example: delete /test/node

        """
        self.zkcli.delete(path)

    def rmr(self, path):
        """Recursively delete all children ZNodes, along with argument node.

        Usage: rmr <path>
        Example: rmr /test

        """
        self.zkcli.delete(path, recursive=True)

    def stat(self, path):
        """Display a ZNode's metadata

        Usage: stat <path>
        Example: stat /test

        """
        def dtfmt(ts):
            return datetime.datetime.fromtimestamp(ts / 1000).strftime(
                "%a %b %d %H:%M:%S UTC %Y")
        stat = self.zkcli.stat(path)
        lines = [
            'cZxid = {0:x}'.format(stat.czxid),
            'ctime = {}'.format(dtfmt(stat.ctime)),
            'mZxid = {0:x}'.format(stat.mzxid),
            'mtime = {}'.format(dtfmt(stat.mtime)),
            'pZxid = {0:x}'.format(stat.pzxid),
            'cversion = {}'.format(stat.cversion),
            'dataVersion = {}'.format(stat.version),
            'aclVersion = {}'.format(stat.aversion),
            'ephemeralOwner = {0:x}'.format(stat.ephemeralOwner),
            'dataLength = {}'.format(stat.dataLength),
            'numChildren = {}'.format(stat.numChildren),
        ]
        return '\n'.join(lines)

    @validate_command_input
    def run(self, command_str):
        if command_str:
            tokens = self._tokenize(command_str)
            command, args = tokens[0], tokens[1:]
            out = getattr(self, command)(*args)
            return out

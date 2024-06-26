#!/usr/bin/python3
# Copyright (c) 2010 Alon Swartz <alon@turnkeylinux.org>
# Added ssh keygen using same password. 2013 John Carver <dude4linux@gmail.com>
#
"""Set account password and generate ssh key

Arguments:
    username      username of account to set password for

Options:
    -p --pass=    if not provided, will ask interactively
"""

import sys
import getopt
import subprocess
from subprocess import PIPE
import signal
import pipes
import bcrypt

from libinithooks.dialog_wrapper import Dialog
from mysqlconf import MySQL


def fatal(s):
    print("Error:", s, file=sys.stderr)
    sys.exit(1)


def usage(s=None):
    if s:
        print("Error:", s, file=sys.stderr)
    print("Syntax: %s <username> [options]" % sys.argv[0], file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(1)


def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hp:", ['help', 'pass='])
    except getopt.GetoptError as e:
        usage(e)

    if len(args) != 1:
        usage()

    username = args[0]
    password = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-p', '--pass'):
            password = val

    if not password:
        d = Dialog('TurnKey Linux - First boot configuration')
        password = d.get_password(
            "%s Password" % username.capitalize(),
            "Please enter new password for the %s user account. This password"
            " will also be used for the Sempahore 'admin' user." % username)

    command = ["chpasswd"]
    input = ":".join([username, password])

    salt = bcrypt.gensalt()
    hashpass = bcrypt.hashpw(password.encode('utf8'), salt).decode('utf8')

    m = MySQL()
    m.execute('UPDATE semaphore.user SET password=%s WHERE id=1;', (hashpass,))

    p = subprocess.Popen(command, stdin=PIPE, shell=False)
    p.stdin.write(input.encode())
    p.stdin.close()
    err = p.wait()
    if err:
        fatal(err)

    """use ssh-keygen to create an rsa key pair using the same password"""
    subprocess.call(['su', username, '-c',
                     'ssh-keygen -q -b 4096 -t rsa -f $HOME/.ssh/id_rsa -N %s'
                     % pipes.quote(password)])
    if err:
        fatal(err)


if __name__ == "__main__":
    main()

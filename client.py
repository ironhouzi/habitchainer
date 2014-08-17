#!/usr/bin/env python3
import socket
import json
import sys
import re
import os
from argparse import ArgumentParser

rcdir = os.path.expandvars("$HOME/.config/habitchainer/")
rcfile = "hcrc"
dirtyfile = "dirty"
rcpath = rcdir + rcfile

def mainPrompt(dailystatus, chaincount):
    prompts = [
        r'∙ ∙ ∙',
        r'∙ ∙%F{220}★ %F{255}',
        r'∙%F{220}★ %F{255}∙',
        r'∙%F{220}★★  %F{255}',
        r'%F{220}★ %F{255}∙ ∙',
        r'%F{220}★ %F{255}∙ %F{220}★ %F{255}',
        r'%F{220}★★  %F{255}∙',
        r'%F{220}★★★   %F{255}']

    return ''.join([prompts[dailystatus], '%F{255}',
                   chainCount(chaincount), ' '])


def chainCount(daycount):
    """ Input: number of days in current chain (int)
        Output: pretty glyph representing this number"""
    if daycount == 0:
        ordval = ord('\u24ea')
    elif daycount <= 20:
        ordval = ord('\u245f') + daycount
    elif daycount <= 35:
        ordval = ord('\u3251') - 21 + daycount
    elif daycount <= 50:
        ordval = ord('\u32b1') - 36 + daycount

    return chr(ordval)


def main(args):
    parser = ArgumentParser()
    message = None
    jsonRegex = re.compile(r'^\{|\[.*\]|\}$')
    host = '192.168.1.117'
    parser.add_argument("command", help="Specifies the return value.")
    parser.add_argument("--host", help="Provide ip address or host name.")
    args = parser.parse_args()

    if args.host:
        host = args.host

    if not os.path.isdir(rcdir):
        os.makedirs(rcdir)

    if os.path.isfile(rcpath):
        if args.host:
            with open(rcpath, 'w') as f:
                f.write(json.dumps([args.host]))
        else:
            with open(rcpath, 'r') as f:
                info = json.loads(f.readline())
                host = info[0]

    message = json.dumps((args.command, ))
    isnumRegex = re.compile(r'^[0,1,2]\d{2}.')

    if not isnumRegex.match(host):
        host = socket.gethostbyname(host)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((host, 13373))
    except:
        sys.exit()

    s.send(bytes(message, 'UTF-8'))
    reply = s.recv(1024).decode('UTF-8')

    if jsonRegex.match(reply):
        reply = json.loads(reply)

        if reply[0] == 'prompt':
            print(mainPrompt(reply[1], reply[2]))
        elif reply[0] == 'next':
            print(reply[1], '- Deadline:', reply[2])

    s.close()

# def offlineMode():
#     dirtypath = rcdir + dirtyfile
#     if os.path.isfile(dirtypath):
#         pass
#     else:
#         with open(dirtypath, 'w') as f:
#             status = ['prompt',
#             f.write(


if __name__ == '__main__':
    main(sys.argv)

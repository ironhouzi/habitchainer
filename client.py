#!/usr/bin/env python3
import socket
import json
import sys
import re

def mainPrompt(dailystatus, chaincount):
    prompts = [
        r'∙ ∙ ∙',
        r'∙ ∙%F{220}★ %F{255}',
        r'∙%F{220}★ %F{255}∙',
        r'∙%F{220}★★  %F{255}',
        r'%F{220}★ %F{255}∙ ∙',
        r'%F{220}★ %F{255}∙ %F{220}★ %F{255}',
        r'%F{220}★★  %F{255}∙',
        r'%F{220}★★★   %F{255}' ]

    return ''.join([prompts[dailystatus], '%F{255}',
                   chainCount(chaincount), ' '])

def chainCount(daycount):
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
    message = None
    jsonRegex = re.compile(r'^\{|\[.*\]|\}$')

    message = json.dumps((args[1], ))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('192.168.1.130', 13373))
    s.send(bytes(message, 'UTF-8'))
    reply = s.recv(1024).decode('UTF-8')

    if jsonRegex.match(reply):
        reply = json.loads(reply)

        if reply[0] == 'prompt':
            print(mainPrompt(reply[1], reply[2]))
        elif reply[0] == 'habit':
            print(reply[1], '-', reply[2])

    s.close()


if __name__ == '__main__':
    main(sys.argv)

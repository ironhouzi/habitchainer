import socket
import json
import habitchainer
import sys


def main(args):
    message = ''
    schedule = habitchainer.Schedule()
    orgfilepath = '/home/dorbin/docs/org-files/schedule.org'
    schedule.parseOrgFile(orgfilepath)

    # conffile = 'habitrc'
    # confpath = '~/.habitchainer/'

    # f = open(confpath + conffile, 'r')
    # orgfilepath = f.readline()
    # f.close()

    if args[1] == 'done':
        task = schedule.getCurrentTask
        message = json.dumps((args[1], task.name))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 13373))
    s.send(bytes(message, 'UTF-8'))
    print('sent')
    result = json.loads(s.recv(1024).decode('UTF-8'))
    print(result)
    s.close()

if __name__ == '__main__':
    main(sys.argv)

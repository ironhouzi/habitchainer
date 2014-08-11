#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import habitchainer
import sys
import json
import re


# This is just about the simplest possible protocol
class Respond(Protocol):
    jsonRegex = re.compile(r'^\{|\[.*\]|\}$')

    def dataReceived(self, data):
        """
        """
        datastring = data.decode('UTF-8').strip()

        if datastring == 'status':
            print(datastring)
            jsonstring = self.factory.schedule.getCurrentTask().jsonEncode()
            self.transport.write(jsonstring)
        elif self.jsonRegex.match(datastring):
            self.factory.schedule.completeCurrentTask()
            task = self.factory.schedule.getCurrentTask()

            if task:
                jsonstring = task.jsonEncode()
                self.transport.write(jsonstring)
            else:
                self.transport.write(bytes('alldone', 'UTF-8'))
        else:
            print("else")


class ScheduleFactory(Factory):
    protocol = Respond

    def __init__(self, schedule):
        self.schedule = schedule


def main(args):
    schedule = habitchainer.Schedule()
    schedule.parseOrgFile(args[2])
    schedf = ScheduleFactory(schedule)
    reactor.listenTCP(int(args[1]), schedf)
    reactor.run()

if __name__ == '__main__':
    main(sys.argv)

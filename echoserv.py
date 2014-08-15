#!/usr/bin/env python3

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, defer
import habitchainer
import sys
import json
import re
import arrow


class Respond(Protocol):
    jsonRegex = re.compile(r'^\{|\[.*\]|\}$')

    def encodeUTF(self, string):
        return bytes(string, "UTF-8")

    def dataReceived(self, data):
        datastring = data.decode('UTF-8').strip()
        structure = json.loads(datastring)

        if structure[0] == 'prompt':
            self.sendStatus()
        elif structure[0] == 'done':
            self.factory.schedule.completeCurrentTask()
            self.sendCommand('OK')
        elif structure[0] == 'next':
            self.sendNextHabit()
        else:
            self.sendCommand('nop')

    def sendNextHabit(self):
        jsonobject = ['next']
        habit = self.factory.schedule.getPendingHabit()
        jsonobject.append(habit.name)
        jsonobject.append(habit.deadline.format('HH:mm'))
        self.transport.write(self.encodeUTF(json.dumps(jsonobject)))

    def sendCommand(self, command):
        self.transport.write(self.encodeUTF(json.dumps([command])))

    def sendStatus(self):
        promptstatus = self.factory.schedule.getDailyStatus()
        chainlength = self.factory.chainlength
        jsonstring = json.dumps(['prompt', promptstatus, chainlength])
        self.transport.write(self.encodeUTF(jsonstring))


class ScheduleFactory(Factory):
    protocol = Respond

    def __init__(self, schedule, chainlength, orgfile):
        self.schedule = schedule
        self.chainlength = chainlength
        self.orgfile = orgfile
        self.d = self.updateSchedule(10)
        self.d.addCallback(self.newDay)

    def updateSchedule(self, timeout):
        d = defer.Deferred()
        reactor.callLater(timeout, self.newDay)
        return d

    def newDay(self):
        if self.schedule.getDailyStatus() == 7:
            self.chainlength += 1
        else:
            self.chainlength = 0

        self.schedule = habitchainer.Schedule()
        self.schedule.parseOrgFile(self.orgfile)
        # self.updateSchedule(self.secondsToMidnight())
        self.updateSchedule(10)

    def secondsToMidnight(self):
        now = arrow.now()
        midnight = now.replace(days=+1, hour=0, minute=1)
        return (midnight - now).seconds


class HabitServer(object):
    """
    Input: (port, orgfile)
    """
    def __init__(self, args):
        self.schedule = habitchainer.Schedule()
        self.orgfile = args[2]
        self.schedule.parseOrgFile(self.orgfile)
        self.port = int(args[1])

    def run(self):
        schedf = ScheduleFactory(self.schedule, 0, self.orgfile)
        reactor.listenTCP(self.port, schedf)
        reactor.run()


def main(args):
    server = HabitServer(args)
    server.run()

if __name__ == '__main__':
    main(sys.argv)

import heapq
import sys
import re
import arrow
import json


class Habit(object):
    keys = ['name', 'deadline', 'scheduled', 'recurrence']

    def __init__(self, name=None, deadline=None,
                 scheduled=None, recurrence=None):
        self._name = name
        self._deadline = deadline
        self._scheduled = scheduled
        self._recurrence = recurrence

    @property
    def name(self):
        """Habit name."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def deadline(self):
        """Habit deadline."""
        return self._deadline

    @deadline.setter
    def deadline(self, value):
        self._deadline = value

    @property
    def scheduled(self):
        """Habit scheduled"""
        return self._scheduled

    @scheduled.setter
    def scheduled(self, value):
        self._scheduled = value

    @property
    def recurrence(self):
        """Habit recurrence."""
        return self._recurrence

    @recurrence.setter
    def recurrence(self, value):
        self._recurrence = value

    def jsonEncode(self):
        scheduled = None

        if self.scheduled:
            scheduled = self.scheduled.timestamp

        values = [self.name, self.deadline.timestamp,
                  scheduled, self.recurrence]
        result = dict(zip(self.keys, values))
        return json.dumps(result)

    def jsonDecode(self, jsonString):
        datadict = json.loads(jsonString)
        self.name = datadict[self.keys[0]]
        self.scheduled = datadict[self.keys[1]]
        self.deadline = datadict[self.keys[2]]
        self.recurrence = datadict[self.keys[3]]


class Schedule(object):
    def __init__(self):
        self.pendingTasks = []
        self.completedTasks = []
        self.time = arrow.utcnow()
        self.currentTask = None

    def scheduleDay(self):
        """Returns day in three letter format."""
        return self.time.format('ddd')

    def scheduleDate(self):
        """Returns tuple: (YYYY, M, D)"""
        return self.time.date()

    def enqueue(self, habit):
        heapq.heappush(self.pendingTasks, (habit.deadline.timestamp, habit))

    def dequeue(self):
        try:
            return (heapq.heappop(self.pendingTasks)[1], arrow.utcnow())
        except IndexError:
            return None

    def completeCurrentTask(self):
        self.completedTasks.append(self.currentTask)
        self.currentTask = self.dequeue()

    def getCurrentTask(self):
        """ Returns None if all tasks are done. """
        if not self.currentTask:
            self.currentTask = self.dequeue()
        return self.currentTask

    def extractTimestamp(self, line):
        """ Input: string. org-mode line containing timestamp.
            Output: (Arrow, string). Date object & recurrence info."""
        # strip from beginning to start of timestamp
        workingline = re.sub(r'^\s+\w+:\s+<', '', line)
        # extract date
        datestring = workingline[:len('YYYY-mm-dd')]
        # cut off day
        workingline = workingline[len(datestring) + len(' Mon '):]
        # extract time
        timestring = workingline[:len('00:00')]
        # get recurrence
        workingline = workingline[len(timestring)+1:]
        recurrencestring = re.sub(r'>\s*$', '', workingline)

        # convert strings to ints
        dateitems = list(map(int, datestring.split('-')))
        timeitems = list(map(int, timestring.split(':')))

        time = arrow.Arrow(dateitems[0], dateitems[1], dateitems[2],
                           timeitems[0], timeitems[1])
        return (time, recurrencestring)

    def extractTaskName(self, line):
        line = re.sub(r'^\*+\s+TODO\s+', '', line)
        line = re.sub(r'\s*(:\w+:\s*)*$', '', line)
        return line

    def newState(self):
        return {'dataStarted': False,
                'dataEnded': False,
                'propertiesStarted': False,
                'propertiesEnded': False}

    def freshState(self, state):
        for k, v in state.items():
            if v:
                return False
        return True

    def dataStateCompleted(self, state):
        return state['dataStarted'] and state['dataEnded']

    def propertyStateCompleted(self, state):
        return state['propertiesStarted'] and state['propertiesEnded']

    def parseOrgFile(self, orgfile):
        sched = r'^\s+SCHEDULED:\s+'
        deadl = r'^\s+DEADLINE:\s+'
        date = r'<\d{4}-\d{2}-\d{2} '
        day = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+'
        time = r'\d{2}:\d{2} '
        rep = r'\+{1,2}\d*[ywmdh]{1}(\s+-\d{1,3}[ywmdh]{1})?>\s*$'

        fileHeaderRegex = re.compile(r'^\*\s+\w+')
        newTaskRegex = re.compile(r'^\*{2,10}\s+TODO\s+(\w+\s*)+\s*(:\w+:)*$')
        taskScheduledRegex = re.compile(sched + date + day + time + rep)
        taskDeadlineRegex = re.compile(deadl + date + day + time + rep)
        propertyStartRegex = re.compile(r'^\s+:PROPERTIES:\s*$')
        propertyRegex = re.compile(r'^\s+:\w+:')
        habitPropertyRegex = re.compile(r'^\s+:STYLE:\s+habit')
        endRegex = re.compile(r'^\s+:END:\s*$')

        f = open(orgfile, 'r')
        title = f.readline()
        habit = Habit()

        if fileHeaderRegex.match(title):
            self.title = title[2:]
        else:
            # TODO error
            print("no fileheader")
            print(title)
            return

        state = self.newState()
        gotData = False
        gotHabitProperty = False

        for line in f:
            if line == '\n':
                continue

            if self.freshState(state) and newTaskRegex.match(line):
                state['dataStarted'] = True
                habit.name = self.extractTaskName(line)
                continue
            elif state['dataStarted'] and taskScheduledRegex.match(line):
                result = self.extractTimestamp(line)
                habit.scheduled = result[0]

                if habit.recurrence and habit.recurrence != result[1]:
                    # TODO: error
                    print("invalid recurrence")
                    return
                elif not habit.recurrence:
                    habit.recurrence = result[1]

                gotData = True
                continue
            elif state['dataStarted'] and taskDeadlineRegex.match(line):
                result = self.extractTimestamp(line)
                habit.deadline = result[0]

                if habit.recurrence and habit.recurrence != result[1]:
                    # TODO: error
                    print("invalid recurrence")
                    return
                elif not habit.recurrence:
                    habit.recurrence = result[1]

                gotData = True
                continue
            elif gotData and state['dataStarted'] and \
                    propertyStartRegex.match(line):
                state['dataEnded'] = True
                state['propertiesStarted'] = True
                continue
            elif state['propertiesStarted'] and gotHabitProperty and \
                    endRegex.match(line):
                self.enqueue(habit)

                if habit.scheduled:
                    sched = habit.scheduled.format('HH:mm - ')
                else:
                    sched = '        '

                print("%s%s : %s" % (sched,
                                     habit.deadline.format('HH:mm'),
                                     habit.name))
                habit = Habit()
                state = self.newState()
                gotData = False
                gotHabitProperty = False
                continue
            elif state['propertiesStarted'] and propertyRegex.match(line):
                if habitPropertyRegex.match(line):
                    gotHabitProperty = True
                continue
            else:
                # TODO error
                print("parseerror!")
                print(line)
                return

            f.close()


def main(args):
    sched = Schedule()
    sched.parseOrgFile(args[1])


if __name__ == '__main__':
    main(sys.argv)

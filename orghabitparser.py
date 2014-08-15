import arrow
import re


class Habit(object):
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


class HabitParser(object):
    def printHabit(self, habit):
        if habit.scheduled:
            sched = habit.scheduled.format('HH:mm - ')
        else:
            sched = '        '

        print("%s%s : %s" % (sched,
                             habit.deadline.format('HH:mm'),
                             habit.name))

    def freshState(self, state):
        for k, v in state.items():
            if v:
                return False
        return True

    def newState(self):
        return {'dataStarted': False,
                'dataEnded': False,
                'propertiesStarted': False,
                'propertiesEnded': False}

    def extractTaskName(self, line):
        line = re.sub(r'^\*+\s+TODO\s+', '', line)
        line = re.sub(r'\s*(:\w+:\s*)*$', '', line)
        return line

    def extractTimestamp(self, line):
        """ Input: string. org-mode line containing timestamp.
            Output: (Arrow, string). Date object & recurrence info.
            Sample org item:

        """

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

    def parseOrgFile(self, orgfile):
        """ Sample orgfile entry:
----------------
** TODO Clean kitchen and livingroom				      :DAILY:
   SCHEDULED: <2014-07-28 Mon 22:00 ++d>
   DEADLINE:  <2014-07-28 Mon 23:00 ++d>
   :PROPERTIES:
   :STYLE:    habit
   :END:
----------------
        Required: - ** TODO (Note there must be atleast two '*' characters)
                  - deadline
                  - timestamp
                  - recurrence (++d)
                  - 'habit' style property
        Scheduled entry is optional.
        NOTE: Only supports daily habits.
        NOTE2: The queue will sort by deadline, but falls back to scheduled
        if two deadlines are identical. Therefore two habits cannot have
        identical scheduled times.
        """

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
                self.deadlines.append(habit.deadline)
                # self.printHabit(habit)
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

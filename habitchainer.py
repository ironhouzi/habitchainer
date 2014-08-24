import heapq
import sys
import arrow
from orghabitparser import HabitParser

# TODO: Add timezone from client request


class Schedule(HabitParser):
    def __init__(self):
        self.pendingTasks = []
        self.completedTasks = []
        self.deadlines = []
        self.time = arrow.utcnow()
        self.allDone = False
        self.remainingTasks = 0
        self.chainlength = 0

    def enqueue(self, habit):
        """Inserts into the heapq: (timestamp, habit). The heapq priority is
           ordered by timestamp, hence no two timestamps can be identical."""
        timestamp = ''

        if habit.scheduled:
            timestamp = habit.scheduled.timestamp
        else:
            timestamp = habit.deadline.timestamp

        heapq.heappush(self.pendingTasks, (timestamp, habit))
        self.remainingTasks += 1

    def dequeue(self):
        try:
            item = heapq.heappop(self.pendingTasks)[1]
            self.remainingTasks -= 1

            if not self.allDone and self.remainingTasks == 0:
                self.allDone = True
                self.chainlength += 1

            return item
        except IndexError:
            pass
        except TypeError:
            print("Error! : Check if two tasks have the same scheduled time.")
            sys.exit()

    def completeCurrentTask(self):
        habit = self.dequeue()

        if not habit and not self.allDone:
            print("Queue error!")

        if habit:
            currentTime = arrow.now('Europe/Oslo')
            print("Completed:", habit.name, "@",
                  currentTime.format('HH:mm'), "w/ deadline:",
                  habit.deadline.format('HH:mm'))
            self.completedTasks.append((habit, currentTime.timestamp, ))

    def period(self, hour):
        """ Input: int representing hour (0-23)
            Returns: the number representing the daily time period.
            (morning, midday, evening)."""
        if (1 < hour < 9):
            return 0
        elif (8 < hour < 18):
            return 1
        elif (17 < hour <= 23):
            return 2

    def getDailyStatus(self):
        """This status represents the completion of the three daily time
        periods: morning (0), day (1), evening (2), are  represented in binary
        values (4, 2, 1, respectively).
        Returns: the sum of these values (0-7), just like a linux file
        permission value (eg. as in: 'chmod 755'). """
        distribution = [0, 0, 0]

        for time in self.deadlines:
            distribution[self.period(time.hour)] += 1

        for task in self.completedTasks:
            deadline = task[0].deadline
            today = arrow.get(task[1]).date()
            deadline = deadline.replace(month=today.month, day=today.day)
            currentTime = arrow.Arrow.fromtimestamp(task[1])

            print(today, deadline, currentTime,
                  self.period(deadline.hour))

            if deadline > currentTime:
                distribution[self.period(deadline.hour)] -= 1

        values = (4, 2, 1,)
        result = 0

        print(distribution)
        for i, f in enumerate(distribution):
            if f == 0:
                result += values[i]

        return result

    def getPendingHabit(self):
        habit = self.dequeue()

        if habit:
            self.enqueue(habit)
            print(habit.name)

        return habit


def main(args):
    sched = Schedule()
    sched.parseOrgFile(args[1])


if __name__ == '__main__':
    main(sys.argv)

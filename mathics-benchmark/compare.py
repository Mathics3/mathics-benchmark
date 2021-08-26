import timeit
from mathics.session import MathicsSession
from mathics.core.parser import parse, MathicsSingleLineFeeder
from expressions import expressions
from functools import reduce
import numpy as np
import matplotlib.pyplot as plt

session = MathicsSession(add_builtin=True, catch_interrupt=False)
number = 100

times = []

with open("bump", "r") as file:
    for key, value in expressions.items():
        expr = parse(session.definitions, MathicsSingleLineFeeder(value))

        times.append(float(file.readline()) - timeit.timeit(lambda: expr.evaluate(session.evaluation), number=number))

# biggest 5 differences in seconds
top_5 = [0, 0, 0, 0, 0]
for time in times:
    for i in range(5):
        if abs(time) > abs(top_5[i]):
            top_5[i] = time

top_5_percentage = []
old_time = []
names = []

for time, i in enumerate(top_5):
    if time == 0:
        break

    old_time.append(times[times.index(time)])

    # difference in percentage of old and new
    top_5_percentage.append(1 - old_time/time)

    names.append(expressions[times.index(time)])

x = np.arange(len(names))  # the label locations
width = 0.35  # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(x - width/2, old_time, width, label='old')
rects2 = ax.bar(x + width/2, time, width, label='new')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('seconds')
ax.set_title('new vs old')
ax.set_xticks(x)
ax.set_xticklabels(names)
ax.legend()

ax.bar_label(rects1, padding=3)
ax.bar_label(rects2, padding=3)

fig.tight_layout()

plt.savefig('report.png')

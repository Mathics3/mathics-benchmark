import timeit
from mathics.session import MathicsSession
from mathics.core.parser import parse, MathicsSingleLineFeeder
from expressions import expressions
from functools import reduce
import numpy as np
import matplotlib.pyplot as plt

session = MathicsSession(add_builtin=True, catch_interrupt=False)
number = 100

old_times = []
new_times = []

with open("bump", "r") as file:
    for key, value in expressions.items():
        expr = parse(session.definitions, MathicsSingleLineFeeder(value))

        old_times.append(float(file.readline()))
        new_times.append(timeit.timeit(lambda: expr.evaluate(session.evaluation), number=number))

# biggest 5 differences in seconds
differences = [abs(old_time - new_time) for old_time, new_time in zip(old_times, new_times)]

top_5_differences = sorted(differences, reverse=True)[:5]

top_5_indices = [
    differences.index(top_5_differences[0]),
    differences.index(top_5_differences[1]),
    differences.index(top_5_differences[2]),
    differences.index(top_5_differences[3]),
    differences.index(top_5_differences[4]),
]

old_times_5 = []
new_times_5 = []
names = []

for index in top_5_indices:
    old_times_5.append(old_times[index])
    new_times_5.append(new_times[index])

    names.append(list(expressions)[index])

x = np.arange(len(names))  # the label locations
width = 0.35  # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(x - width/2, old_times_5, width, label='old')
rects2 = ax.bar(x + width/2, new_times_5, width, label='new')

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

import timeit
from mathics.session import MathicsSession
from mathics.core.parser import parse, MathicsSingleLineFeeder
from expressions import expressions

session = MathicsSession(add_builtin=True, catch_interrupt=False)
number = 100

with open("bump", "w") as file:
    for key, value in expressions.items():
        expr = parse(session.definitions, MathicsSingleLineFeeder(value))

        file.write(f"{timeit.timeit(lambda: expr.evaluate(session.evaluation), number=number):.10f}\n")

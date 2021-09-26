from mathics.session import MathicsSession
from collections import defaultdict

session = MathicsSession(add_builtin=True, catch_interrupt=False)

function_counts = defaultdict(lambda: 0)


def trace_apply(func, builtin_name):
    """
    This is an example kind of thing we might want to do in tracing a function.
    Here we are just getting a count of calls.
    """

    def count_apply(*args, **kwargs):
        function_counts[builtin_name] += 1
        func(*args, **kwargs)

    return count_apply


def wrap_definitions(definitions):
    """
    This is an example to show how we can instrument or decorate built-in funcitons
    to get specific characteristics of them.
    """
    for builtin_name, definition in definitions.builtin.items():
        for rule in definition.downvalues:
            # Some rules don't have functions associated with them
            if hasattr(rule, "function"):
                func = rule.function
                if func.__name__ in ("apply_with_prec",):
                    continue
                rule.function = trace_apply(func, builtin_name)
            else:
                # FIXME figure out how to deal with operators
                pass


wrap_definitions(session.evaluation.definitions)


def evaluate(str_expr: str):
    return session.evaluate(str_expr)


for str_expr in [
    "1 + 2",
    "1 + 2 + 3",
    "1 + 2 + b",
    "a + b + 3",
    "1234567890 + 2345678901",
    "a + b + 4.5 + a",
    "D[x^3 + x^2, x]",  # We are not getting D because it is an operator
    "Array[f, 4]",
    "Range[0, 2, 1/3]",
]:
    evaluate(str_expr)

for name, count in function_counts.items():
    print("%4d %s" % (count, name))

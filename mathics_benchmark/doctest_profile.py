import sys
import trace
import cProfile
import pickle

import pstats
from pstats import SortKey


import mathics.docpipeline as docpipeline


profile_file = "docpipeline-profile.log"


def build_title(t):
    if t is str:
        t = t.split("\t")
    return "\n|\t" + "\t|\t".join(t) + "\t|" + "\n" + "|" + 6 * "  ----- |   " + "\n"


def showdataline(d):
    return "|" + ("\t|".join([str(c) for c in d])) + "|\n"


def build_table(title, data):
    table = showtitle(title)
    for d in data:
        table += showdataline(d)
    return table


def normalize_col(s):
    s = s.strip()
    new_s = None
    while True:
        new_s = s
        new_s = new_s.replace("\t\t", "\t")
        new_s = new_s.replace("  ", "\t")
        new_s = new_s.replace("\t ", "\t")
        new_s = new_s.replace(" \t", "\t")
        if new_s is s:
            break
        s = new_s
    row = s.split(" ")
    if row[1][0] in ("0123456789"):
        s = row[0] + "\t" + row[1] + "\t" + " ".join(row[2:])
    return s.split("\t")

if False:
    cProfile.run(
        compile("docpipeline.main()", "fake", "exec", optimize=2), filename=profile_file
    )

p = pstats.Stats(profile_file)
p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()

sys.exit()

with open(profile_file, "r") as f:
    s = f.readline()
    s = normalize_cols(s)
    titles = s.strip().split("\t")
    data = []
    for s in f.readlines():
        row = normalize_col(s)
        if len(row) != 6:
            print(s, " couldn't be interpreted")
            continue
        row = row[0].split("/")[0]
        row = (
            int(row[0]),
            float(row[1]),
            float(row[2]),
            float(row[3]),
            float(row[4]),
            row[5],
        )
        data.append(row)

with open("profile_file.pkl", "wb") as f:
    pickle.dump(data, f)


print("Most called functions")
print("=====================\n")
print(build_table(titles, sorted(data, key=lambda x: -x[0])[:20]))


print("Most time comsuming functions")
print("=====================\n")
print(build_table(titles, sorted(data, key=lambda x: -x[1])[:20]))

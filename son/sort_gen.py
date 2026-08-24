from itertools import combinations

TOTAL_SET = 40
LENGTH = 6
OUTPUT_FILE = "temp.txt"

with open(OUTPUT_FILE, "w") as f:
    for combo in combinations(range(1, TOTAL_SET + 1), LENGTH):
        f.write("{" + ",".join(map(str, combo)) + "}\n")

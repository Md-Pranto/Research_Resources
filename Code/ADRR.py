# ADRR Scheduling Algorithm

def calculate_mean(lst):
    return sum(lst) / len(lst) if lst else 0


print("=== ADRR Scheduling ===")

# ---------------- INPUT ----------------
n = int(input("Enter number of processes: "))
processes = []
predicted_list = []
for i in range(n):
    line = input().split()
    name = line[0]
    arrival = float(line[1])
    burst = float(line[2])
    predicted_bt = float(burst * 1.1)  # fake ML
    processes.append([name, arrival, burst, predicted_bt])
    predicted_list.append(predicted_bt)

processes.sort(key=lambda x: x[1])

# ---------------- ADRR PREP ----------------
sorted_bt = sorted(predicted_list)
diff = [0] * n
for i in range(1, n):
    diff[i] = abs(sorted_bt[i] - sorted_bt[i - 1])
base_tq = calculate_mean(sorted_bt)

# ---------------- INITIALIZATION ----------------
remaining = {}
completion = {}

for p in processes:
    name = p[0]
    remaining[name] = p[2]
    completion[name] = 0

time = 0
queue = []
completed = 0
index = 0
context_switches = 0

# ---------------- MAIN LOOP ----------------
while completed < n:
    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1

    if len(queue) == 0:
        time += 1
        continue

    current = queue.pop(0)
    name = current[0]

    # Elastic TQ
    pred_bt = current[3]
    try:
        pos = sorted_bt.index(pred_bt)
    except ValueError:
        pos = 0  # safety for duplicates
    elastic_tq = base_tq + diff[pos]
    if elastic_tq > remaining[name]:
        elastic_tq = remaining[name]

    start = time
    time += elastic_tq
    remaining[name] -= elastic_tq

    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1

    if remaining[name] > 0:
        queue.append(current)
        context_switches += 1
    else:
        completion[name] = time
        completed += 1
        context_switches += 1

# ---------------- METRICS ----------------
total_wait = 0
total_tat = 0
for p in processes:
    name = p[0]
    arrival = p[1]
    burst = p[2]
    wt = completion[name] - arrival - burst
    total_wait += wt
    tat = completion[name] - arrival
    total_tat += tat

avg_wait = total_wait / n
avg_tat = total_tat / n


print("\nAverage Waiting Time:", round(avg_wait, 2))
print("Average Turnaround Time:", round(avg_tat, 2))
print("Context Switches:", context_switches)
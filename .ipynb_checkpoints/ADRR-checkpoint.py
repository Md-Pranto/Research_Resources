# ------------------------------------------------------------------------------
# ADRR with YOUR Jain's Fairness Index (Efficiency Ratio)
# Now uses xi = acc_cpu / (acc_cpu + acc_wait)  ← same as FRD-RR
# ------------------------------------------------------------------------------

def calculate_mean(lst):
    return sum(lst) / len(lst) if lst else 0


# YOUR Jain's Fairness Index (Efficiency ratio) - same as FRD-RR
def calculate_jains_fairness_index(acc_cpu, acc_wait, processes):
    n = len(processes)
    if n == 0:
        return 1.0
    xi_list = []
    for p in processes:
        name = p[0]
        cpu = acc_cpu.get(name, 0)
        wait = acc_wait.get(name, 0)
        xi = cpu / (cpu + wait) if (cpu + wait) > 0 else 0.5
        xi_list.append(xi)

    sum_xi = sum(xi_list)
    sum_xi_squared = sum(x * x for x in xi_list)
    if sum_xi_squared == 0:
        return 1.0
    return (sum_xi * sum_xi) / (n * sum_xi_squared)


print("=== ADRR Scheduling (using YOUR efficiency JFI) ===")

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
acc_cpu = {}
acc_wait = {}  # ← needed for YOUR JFI
last_end_time = {}

for p in processes:
    name = p[0]
    remaining[name] = p[2]
    completion[name] = 0
    acc_cpu[name] = 0
    acc_wait[name] = 0
    last_end_time[name] = p[1]

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

    # Waiting time accumulation (required for YOUR JFI)
    wait_increment = time - last_end_time[name]
    acc_wait[name] += wait_increment

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
    acc_cpu[name] += elastic_tq
    last_end_time[name] = time

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

# YOUR JFI (now used on ADRR)
final_jfi = calculate_jains_fairness_index(acc_cpu, acc_wait, processes)

print("\nAverage Waiting Time:", round(avg_wait, 2))
print("Average Turnaround Time:", round(avg_tat, 2))
print("Context Switches:", context_switches)
print("Final Fairness Index (YOUR efficiency JFI):", round(final_jfi, 4))

print("\nNote: JFI now uses same definition as FRD-RR → fair comparison!")
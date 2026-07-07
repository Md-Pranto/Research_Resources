# ------------------------------------------------------------------------------
# EImHLVQTRR (Enhanced Improved Half-Life Variable Quantum Time RR)
# Using YOUR Jain's Fairness Index (Efficiency Ratio) from FRD-RR
# TQ = sqrt(average BT * minimum BT) from CURRENT RQ (dynamic per round)
# Input/Output EXACTLY same as your ADRR code
# ------------------------------------------------------------------------------

import math
from collections import deque

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

print("=== EImHLVQTRR Scheduling (using YOUR efficiency JFI) ===")

# ---------------- INPUT ----------------
n = int(input("Enter number of processes: "))
processes = []
for i in range(n):
    line = input().split()
    name = line[0]
    arrival = float(line[1])
    burst = float(line[2])
    processes.append([name, arrival, burst])  # No predicted_bt needed

processes.sort(key=lambda x: x[1])  # Sort by arrival time (FCFS order)

# ---------------- INITIALIZATION ----------------
remaining = {}
completion = {}
acc_cpu = {}
acc_wait = {}          # ← needed for YOUR JFI
last_end_time = {}

for p in processes:
    name = p[0]
    remaining[name] = p[2]
    completion[name] = 0
    acc_cpu[name] = 0
    acc_wait[name] = 0
    last_end_time[name] = p[1]

time = 0
queue = deque()        # Use deque for efficient popleft (FCFS)
completed = 0
index = 0              # For adding arrivals
context_switches = 0

# ---------------- MAIN LOOP ----------------
while completed < n:
    # Add newly arrived processes to queue (FCFS)
    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1
    
    if len(queue) == 0:
        time += 1
        continue
    
    # Get current process (popleft for FCFS order)
    current = queue.popleft()
    name = current[0]
    
    # Waiting time accumulation (required for YOUR JFI)
    wait_increment = time - last_end_time[name]
    acc_wait[name] += wait_increment
    
    # ---------------- DYNAMIC TQ (EImHLVQTRR) ----------------
    # Collect remaining BTs from CURRENT queue + current process
    current_rbt_list = [remaining[p[0]] for p in list(queue)] + [remaining[name]]
    if not current_rbt_list:
        tq = 1  # Safety fallback
    else:
        avg_bt = calculate_mean(current_rbt_list)
        min_bt = min(current_rbt_list)
        tq = math.sqrt(avg_bt * min_bt)
        tq = max(1, math.ceil(tq))  # At least 1ms, ceil as per PDF examples
    
    # Cap TQ to remaining BT of current process
    if tq > remaining[name]:
        tq = remaining[name]
    
    # Execute for TQ
    start = time
    time += tq
    remaining[name] -= tq
    acc_cpu[name] += tq
    last_end_time[name] = time
    
    # Add new arrivals during this execution
    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1
    
    # Check if process completed
    if remaining[name] > 0:
        queue.append(current)  # Re-queue at tail
        context_switches += 1
    else:
        completion[name] = time
        completed += 1
        context_switches += 1  # Completion also counts as a switch

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

# YOUR JFI (now used on EImHLVQTRR)
final_jfi = calculate_jains_fairness_index(acc_cpu, acc_wait, processes)

print("\nAverage Waiting Time:", round(avg_wait, 2))
print("Average Turnaround Time:", round(avg_tat, 2))
print("Context Switches:", context_switches)
print("Final Fairness Index (YOUR efficiency JFI):", round(final_jfi, 4))

print("\nNote: JFI now uses same definition as FRD-RR → fair comparison!")
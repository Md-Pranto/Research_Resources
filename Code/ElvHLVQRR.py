# EImHLVQTRR (Enhanced Improved Half-Life Variable Quantum Time RR) Scheduling Algorithm

import math
from collections import deque

def calculate_mean(lst):
    return sum(lst) / len(lst) if lst else 0


print("=== EImHLVQTRR Scheduling ===")

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

for p in processes:
    name = p[0]
    remaining[name] = p[2]
    completion[name] = 0

time = 0
queue = deque()        # Use deque for efficient popleft (FCFS)
completed = 0
index = 0              # For adding arrivals
context_switches = 0

# ---------------- MAIN LOOP ----------------
# Load initially arrived
while index < n and processes[index][1] <= time:
    queue.append(processes[index])
    index += 1

while completed < n:
    if len(queue) == 0:
        time = processes[index][1]
        while index < n and processes[index][1] <= time:
            queue.append(processes[index])
            index += 1
    
    # ---------------- DYNAMIC TQ (EImHLVQTRR) ----------------
    # Calculate TQ for this cycle based on current queue
    rbt_list = [remaining[p[0]] for p in list(queue)]
    if not rbt_list:
        tq = 1  # Safety fallback
    else:
        avg_bt = calculate_mean(rbt_list)
        min_bt = min(rbt_list)
        tq = max(1, int(math.sqrt(avg_bt * min_bt)))

    k = len(queue)
    
    for _ in range(k):
        # Get current process (popleft for FCFS order)
        current = queue.popleft()
        name = current[0]
        
        # The paper's termination rule: if P(RBT) <= 1TQ after running for 1TQ
        # meaning if initial RBT <= 2 * TQ, it finishes in one go.
        if remaining[name] <= 2 * tq:
            run_time = remaining[name]
        else:
            run_time = tq
        
        # Execute for run_time
        time += run_time
        remaining[name] -= run_time
        
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

print("\nAverage Waiting Time:", round(avg_wait, 2))
print("Average Turnaround Time:", round(avg_tat, 2))
print("Context Switches:", context_switches)
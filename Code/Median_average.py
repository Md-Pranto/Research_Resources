# Modified Median Mean Round Robin (MMMRR)
# TQ per cycle = (Median + Mean of CURRENT remaining bursts) / 2
# Clean Output Version (Comparison Ready)
# Prints only: AWT, ATT, Context Switches

def calculate_mean(lst):
    if len(lst) == 0:
        return 0
    total = 0
    for x in lst:
        total += x
    return total / len(lst)


def calculate_median(lst):
    if len(lst) == 0:
        return 0
    sorted_lst = sorted(lst)
    n = len(sorted_lst)
    if n % 2 == 1:
        return sorted_lst[n // 2]
    else:
        return (sorted_lst[n//2 - 1] + sorted_lst[n//2]) / 2



print("=== MMMRR Scheduling ===")

n = int(input("Enter number of processes: "))

processes = []

for i in range(n):
    line = input().split()
    name = line[0]
    arrival = float(line[1])
    burst = float(line[2])
    processes.append([name, arrival, burst])


# Sort by arrival
for i in range(n):
    for j in range(i + 1, n):
        if processes[i][1] > processes[j][1]:
            temp = processes[i]
            processes[i] = processes[j]
            processes[j] = temp


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

served_in_cycle = 0

while completed < n:

    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1

    if len(queue) == 0:
        time += 1
        continue

    # Recalculate TQ at start of cycle
    if served_in_cycle == 0 or served_in_cycle >= len(queue):

        current_remaining = []
        for p in processes:
            if remaining[p[0]] > 0:
                current_remaining.append(remaining[p[0]])

        if len(current_remaining) > 0:
            median = calculate_median(current_remaining)
            mean = calculate_mean(current_remaining)
            time_quantum = (median + mean) / 2

            # Round to nearest integer
            if time_quantum % 1 < 0.5:
                time_quantum = float(time_quantum)
            else:
                time_quantum = float(time_quantum) + 1

        served_in_cycle = 0


    current = queue.pop(0)
    name = current[0]

    run_time = time_quantum if remaining[name] > time_quantum else remaining[name]

    time += run_time
    remaining[name] -= run_time

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

    served_in_cycle += 1


# ------------------- CLEAN OUTPUT -------------------

total_wait = 0
for p in processes:
    name = p[0]
    arrival = p[1]
    burst = p[2]
    wt = completion[name] - arrival - burst
    total_wait += wt

print("\nAverage Waiting Time:", total_wait / n if n > 0 else 0)


total_tat = 0
for p in processes:
    name = p[0]
    arrival = p[1]
    tat = completion[name] - arrival
    total_tat += tat

print("\nAverage Turnaround Time:", total_tat / n if n > 0 else 0)


print("\nContext Switches:", context_switches)


print("\nNote: Compare with Standard RR, FRD-RR, and ADRR using same input.")
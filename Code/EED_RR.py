# ------------------------------------------------------------------------------
# Efficiency-Enhanced Dynamic Round Robin Scheduling With Jain's Index and Deficit Based Elastic Time Quantum (EED-RR)
# ------------------------------------------------------------------------------
from collections import deque

# Helper function: calculate mean of a list
def calculate_mean(lst):
    if len(lst) == 0:
        return 0
    total = 0
    for x in lst:
        total += x
    return total / len(lst)

# Helper function: calculate median of a list
def calculate_median(lst):
    if len(lst) == 0:
        return 0
    sorted_lst = sorted(lst)
    n = len(sorted_lst)
    if n % 2 == 1:
        return sorted_lst[n // 2]
    else:
        mid1 = sorted_lst[n // 2 - 1]
        mid2 = sorted_lst[n // 2]
        return (mid1 + mid2) / 2

# Helper function: calculate Jain's Fairness Index
# xi = accumulated_cpu / (accumulated_cpu + waiting)   → efficiency ratio
# lower xi means more starved
def calculate_jains_fairness_index(acc_cpu_dict, wait_dict, process_names):
    n = len(process_names)
    if n == 0:
        return 1.0
    
    xi_list = []
    for name in process_names:
        cpu = acc_cpu_dict.get(name, 0)
        wait = wait_dict.get(name, 0)
        if cpu + wait == 0:
            xi = 0.5  # neutral for processes not started
        else:
            xi = cpu / (cpu + wait)
        xi_list.append(xi)
    
    sum_xi = 0
    sum_xi_squared = 0
    for xi in xi_list:
        sum_xi += xi
        sum_xi_squared += xi * xi
    
    if sum_xi_squared == 0:
        return 1.0
    
    j = (sum_xi * sum_xi) / (n * sum_xi_squared)
    return j

# Main EED-RR simulation
print("=== Efficiency-Enhanced Dynamic Round Robin Scheduling With Jain's Index and Deficit Based Elastic Time Quantum (EED-RR) ===")

# Input
n = int(input("Enter number of processes: "))

processes = []
burst_times_for_base = []  # to calculate base TQ

for i in range(n):
    line = input().split()
    name = line[0]
    arrival = float(line[1])
    burst = float(line[2])
    processes.append([name, arrival, burst])
    burst_times_for_base.append(burst)

# Calculate base time quantum (like MMMRR)
tq_base = (calculate_mean(burst_times_for_base) + calculate_median(burst_times_for_base)) / 2
print(f"Base Time Quantum (TQ_base) = {tq_base:.2f}")

# Sort processes by arrival time
processes.sort(key=lambda x: x[1])

# Data structures (simple dictionaries and lists)
remaining = {}
completion = {}
acc_cpu = {}       # accumulated CPU time per process
acc_wait = {}      # accumulated waiting time per process
last_end_time = {} # when did this process last finish its slice

for p in processes:
    name = p[0]
    remaining[name] = p[2]
    completion[name] = 0
    acc_cpu[name] = 0
    acc_wait[name] = 0
    last_end_time[name] = p[1]  # initially arrival time

time = 0
queue = deque()        # deque for O(1) popleft
gantt = []             # [name, start, end]
completed = 0
index = 0              # next process to consider for arrival
context_switches = 0   # count context switches (preempt or finish)
sum_x = 0.5 * n        # running Σ x_i  (all x_i start at 0.5 since cpu=wait=0)
sum_x2 = 0.25 * n      # running Σ x_i² (0.5² = 0.25)

# Main scheduling loop
while completed < n:
    
    # Add all arrived processes to queue
    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1
    
    # If no process is ready, just advance time
    if len(queue) == 0:
        time += 1
        continue
    
    # Take the first process in queue (RR style)
    current = queue.popleft()
    name = current[0]
    arrival = current[1]
    
    
    cpu_i = acc_cpu[name]
    wait_i = acc_wait[name]
    x_old = cpu_i / (cpu_i + wait_i) if (cpu_i + wait_i) > 0 else 0.5
    
    # Calculate waiting time since last run
    wait_increment = time - last_end_time[name]
    acc_wait[name] += wait_increment
    
    wait_i_new = acc_wait[name]
    x_new = cpu_i / (cpu_i + wait_i_new) if (cpu_i + wait_i_new) > 0 else 0.5
    

    sum_x  += (x_new - x_old)
    sum_x2 += (x_new * x_new - x_old * x_old)
    

    j_current = (sum_x * sum_x) / (n * sum_x2) if sum_x2 > 0 else 1.0
    
    # Average xi and this process's xi (O(1))
    avg_xi = sum_x / n
    my_xi = x_new
    
    # Calculate beta_i (deficit) for this process
    beta = 0
    if my_xi < avg_xi and avg_xi > 0:
        beta = (avg_xi - my_xi) / avg_xi
    
    # Calculate elastic time quantum for this process
    scaling_factor = 1.5
    elastic_tq = tq_base * (1 + (1 - j_current) * beta * scaling_factor)
    if elastic_tq > remaining[name]:
        elastic_tq = remaining[name]
    
    x_old2 = x_new
    
    # Run the process
    start = time
    time += elastic_tq
    acc_cpu[name] += elastic_tq
    remaining[name] -= elastic_tq
    last_end_time[name] = time   # update last end time
    
    cpu_i_after = acc_cpu[name]
    wait_i_after = acc_wait[name]
    x_new2 = cpu_i_after / (cpu_i_after + wait_i_after) if (cpu_i_after + wait_i_after) > 0 else 0.5
    sum_x  += (x_new2 - x_old2)
    sum_x2 += (x_new2 * x_new2 - x_old2 * x_old2)
    
    # Record in Gantt chart
    gantt.append([name, start, time])
    
    # Add any new arrivals during this slice
    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1
    
    # If still remaining burst, put back in queue (preemption)
    if remaining[name] > 0:
        queue.append(current)
        context_switches += 1  # context switch for preemption
    else:
        completion[name] = time
        completed += 1
        context_switches += 1  # context switch for finish (optional, but counts overhead)

# Output results
# print("\nGantt Chart: [process, start time, end time]")
# for g in gantt:
#     print(g)

# print("\nWaiting Time:")
total_wait = 0
for p in processes:
    name = p[0]
    arrival = p[1]
    burst = p[2]
    if name in completion:
        wt = completion[name] - arrival - burst
        # print(name, ":", wt)
        total_wait += wt
    else:
        print(name, ": not completed")

print("\nAverage Waiting Time:", total_wait / n if n > 0 else 0)

# Average Turnaround Time (ATT)
total_turnaround = 0
# print("\nTurnaround Time:")
for p in processes:
    name = p[0]
    arrival = p[1]
    if name in completion:
        tat = completion[name] - arrival
        # print(name, ":", tat)
        total_turnaround += tat
    # else:
    #     print(name, ": not completed")

print("\nAverage Turnaround Time:", total_turnaround / n if n > 0 else 0)

# Context Switches
print("\nContext Switches:", context_switches)

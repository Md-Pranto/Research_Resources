# ------------------------------------------------------------------------------
# Efficiency-Enhanced Dynamic Round Robin Scheduling With Jain's Index and Deficit Based Elastic Time Quantum (EED-RR) - Ablation Ready
# ablation_mode: 0=Base, 1=Base+JFI, 2=Base+JFI+Deficit, 3=Full (default)
# ------------------------------------------------------------------------------
from collections import deque

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
        mid1 = sorted_lst[n // 2 - 1]
        mid2 = sorted_lst[n // 2]
        return (mid1 + mid2) / 2

def calculate_jains_fairness_index(acc_cpu_dict, wait_dict, process_names):
    n = len(process_names)
    if n == 0:
        return 1.0
    
    xi_list = []
    for name in process_names:
        cpu = acc_cpu_dict.get(name, 0)
        wait = wait_dict.get(name, 0)
        if cpu + wait == 0:
            xi = 0.5
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

def run_EED_RR(processes, ablation_mode=3):
    """ablation_mode: 
    0 = Base only
    1 = Base + JFI
    2 = Base + JFI + Deficit
    3 = Full EED-RR (default)"""
    
    n = len(processes)
    processes = [[p[0], float(p[1]), float(p[2])] for p in processes]
    burst_times_for_base = [p[2] for p in processes]

    tq_base = (calculate_mean(burst_times_for_base) + calculate_median(burst_times_for_base)) / 2

    processes.sort(key=lambda x: x[1])

    remaining = {p[0]: p[2] for p in processes}
    completion = {p[0]: 0 for p in processes}
    acc_cpu = {p[0]: 0 for p in processes}
    acc_wait = {p[0]: 0 for p in processes}
    last_end_time = {p[0]: p[1] for p in processes}

    time = 0
    queue = deque()
    completed = 0
    index = 0
    context_switches = 0
    sum_x = 0.5 * n
    sum_x2 = 0.25 * n

    while completed < n:
        while index < n and processes[index][1] <= time:
            queue.append(processes[index])
            index += 1

        if len(queue) == 0:
            time += 1
            continue

        current = queue.popleft()
        name = current[0]

        # Waiting update
        cpu_i = acc_cpu[name]
        wait_i = acc_wait[name]
        x_old = cpu_i / (cpu_i + wait_i) if (cpu_i + wait_i) > 0 else 0.5

        wait_increment = time - last_end_time[name]
        acc_wait[name] += wait_increment

        wait_i_new = acc_wait[name]
        x_new = cpu_i / (cpu_i + wait_i_new) if (cpu_i + wait_i_new) > 0 else 0.5

        sum_x += (x_new - x_old)
        sum_x2 += (x_new * x_new - x_old * x_old)

        j_current = (sum_x * sum_x) / (n * sum_x2) if sum_x2 > 0 else 1.0
        avg_xi = sum_x / n
        my_xi = x_new

        beta = 0
        if my_xi < avg_xi and avg_xi > 0:
            beta = (avg_xi - my_xi) / avg_xi

        # Ablation Mode
        if ablation_mode == 0:           # Base only
            elastic_tq = tq_base
        elif ablation_mode == 1:         # Base + JFI
            elastic_tq = tq_base * (1 + (1 - j_current))
        elif ablation_mode == 2:         # Base + JFI + Deficit
            elastic_tq = tq_base * (1 + (1 - j_current) * beta)
        else:                            # Full EED-RR
            elastic_tq = tq_base * (1 + (1 - j_current) * beta * 1.5)

        if elastic_tq > remaining[name]:
            elastic_tq = remaining[name]

        # Run process
        start = time
        time += elastic_tq
        acc_cpu[name] += elastic_tq
        remaining[name] -= elastic_tq
        last_end_time[name] = time

        # CPU update
        x_old2 = x_new
        cpu_i_after = acc_cpu[name]
        wait_i_after = acc_wait[name]
        x_new2 = cpu_i_after / (cpu_i_after + wait_i_after) if (cpu_i_after + wait_i_after) > 0 else 0.5
        sum_x += (x_new2 - x_old2)
        sum_x2 += (x_new2 * x_new2 - x_old2 * x_old2)

        # Add any new arrivals during this slice
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

    # Final metrics
    total_wait = sum(completion[p[0]] - p[1] - p[2] for p in processes)
    total_tat = sum(completion[p[0]] - p[1] for p in processes)
    final_jfi = calculate_jains_fairness_index(acc_cpu, acc_wait, [p[0] for p in processes])

    return {
        "AWT": total_wait / n if n > 0 else 0,
        "ATT": total_tat / n if n > 0 else 0,
        "CS": context_switches,
        "JFI": final_jfi
    }


# For direct testing
if __name__ == "__main__":
    n = int(input("Enter number of processes: "))
    processes = []
    for i in range(n):
        line = input().split()
        processes.append([line[0], float(line[1]), float(line[2])])
    
    result = run_EED_RR(processes, ablation_mode=3)
    print("\nAWT :", round(result["AWT"], 2))
    print("ATT :", round(result["ATT"], 2))
    print("CS  :", result["CS"])
    print("JFI :", round(result["JFI"], 4))
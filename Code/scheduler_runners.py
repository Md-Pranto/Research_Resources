"""
In-process algorithm runners (same logic as .py files).
Accepts process list [[name, arrival, burst], ...] and returns {AWT, ATT, CS}.
Used for benchmark with 10k processes (faster than subprocess).
"""

import math
from collections import deque


def _mean(lst):
    return sum(lst) / len(lst) if lst else 0


def _median(lst):
    if not lst:
        return 0
    s = sorted(lst)
    n = len(s)
    return (s[n // 2 - 1] + s[n // 2]) / 2 if n % 2 == 0 else s[n // 2]


def _jfi(acc_cpu, acc_wait, process_names):
    n = len(process_names)
    if n == 0:
        return 1.0
    xi_list = []
    for name in process_names:
        c, w = acc_cpu.get(name, 0), acc_wait.get(name, 0)
        xi = c / (c + w) if (c + w) > 0 else 0.5
        xi_list.append(xi)
    s1, s2 = sum(xi_list), sum(x * x for x in xi_list)
    return (s1 * s1) / (n * s2) if s2 else 1.0


def run_MMMRR(processes):
    """Median_average.py logic."""
    processes = [[p[0], float(p[1]), float(p[2])] for p in processes]
    processes.sort(key=lambda x: x[1])
    n = len(processes)
    remaining = {p[0]: p[2] for p in processes}
    completion = {p[0]: 0 for p in processes}
    time, queue, completed, index, context_switches = 0, [], 0, 0, 0
    served_in_cycle = 0
    time_quantum = 1.0

    while completed < n:
        while index < n and processes[index][1] <= time:
            queue.append(processes[index])
            index += 1
        if not queue:
            time += 1
            continue
        rbt = [remaining[p[0]] for p in processes if remaining[p[0]] > 0]
        if served_in_cycle == 0 and rbt:
            time_quantum = (_median(rbt) + _mean(rbt)) / 2
            time_quantum = int(time_quantum) if time_quantum % 1 < 0.5 else int(time_quantum) + 1
            served_in_cycle = 0
        current = queue.pop(0)
        name = current[0]
        run_time = min(time_quantum, remaining[name])
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

    total_wait = sum(completion[p[0]] - p[1] - p[2] for p in processes)
    total_tat = sum(completion[p[0]] - p[1] for p in processes)
    return {"AWT": total_wait / n, "ATT": total_tat / n, "CS": context_switches}


def run_ADRR(processes):
    """ADRR.py logic."""
    processes = [[p[0], float(p[1]), float(p[2]), float(p[2]) * 1.1] for p in processes]
    processes.sort(key=lambda x: x[1])
    n = len(processes)
    pred_list = [p[3] for p in processes]
    sorted_bt = sorted(pred_list)
    diff = [0] + [abs(sorted_bt[i] - sorted_bt[i - 1]) for i in range(1, n)]
    base_tq = _mean(sorted_bt)
    remaining = {p[0]: p[2] for p in processes}
    completion = {p[0]: 0 for p in processes}
    time, queue, completed, index, context_switches = 0, [], 0, 0, 0

    while completed < n:
        while index < n and processes[index][1] <= time:
            queue.append(processes[index])
            index += 1
        if not queue:
            time += 1
            continue
        current = queue.pop(0)
        name = current[0]
        try:
            pos = sorted_bt.index(current[3])
        except ValueError:
            pos = 0
        elastic_tq = min(base_tq + diff[pos], remaining[name])
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

    total_wait = sum(completion[p[0]] - p[1] - p[2] for p in processes)
    total_tat = sum(completion[p[0]] - p[1] for p in processes)
    return {"AWT": total_wait / n, "ATT": total_tat / n, "CS": context_switches}


def run_EED_RR(processes, scaling_factor=1.5):
    """EED_RR.py logic."""
    processes = [[p[0], float(p[1]), float(p[2])] for p in processes]
    processes.sort(key=lambda x: x[1])
    n = len(processes)
    burst_list = [p[2] for p in processes]
    tq_base = (_mean(burst_list) + _median(burst_list)) / 2
    remaining = {p[0]: p[2] for p in processes}
    completion = {p[0]: 0 for p in processes}
    acc_cpu = {p[0]: 0 for p in processes}
    acc_wait = {p[0]: 0 for p in processes}
    last_end = {p[0]: p[1] for p in processes}
    time, queue, completed, index, context_switches = 0, [], 0, 0, 0

    while completed < n:
        while index < n and processes[index][1] <= time:
            queue.append(processes[index])
            index += 1
        if not queue:
            time += 1
            continue
        current = queue.pop(0)
        name = current[0]
        acc_wait[name] += time - last_end[name]
        j_current = _jfi(acc_cpu, acc_wait, [p[0] for p in processes])
        xi_sum = sum((acc_cpu[n] / (acc_cpu[n] + acc_wait[n]) if (acc_cpu[n] + acc_wait[n]) > 0 else 0.5) for n in acc_cpu)
        avg_xi = xi_sum / len(acc_cpu) if acc_cpu else 0.5
        my_sum = acc_cpu[name] + acc_wait[name]
        my_xi = acc_cpu[name] / my_sum if my_sum > 0 else 0.5
        beta = (avg_xi - my_xi) / avg_xi if my_xi < avg_xi and avg_xi else 0
        elastic_tq = min(tq_base * (1 + (1 - j_current) * beta * scaling_factor), remaining[name])
        time += elastic_tq
        acc_cpu[name] += elastic_tq
        remaining[name] -= elastic_tq
        last_end[name] = time
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

    total_wait = sum(completion[p[0]] - p[1] - p[2] for p in processes)
    total_tat = sum(completion[p[0]] - p[1] for p in processes)
    return {"AWT": total_wait / n, "ATT": total_tat / n, "CS": context_switches}


def run_ElvHLVQRR(processes):
    processes = [[p[0], float(p[1]), float(p[2])] for p in processes]
    processes.sort(key=lambda x: x[1])
    n = len(processes)
    remaining = {p[0]: p[2] for p in processes}
    completion = {p[0]: 0 for p in processes}
    time, completed, index, context_switches = 0, 0, 0, 0
    queue = deque()

    # Load initially arrived
    while index < n and processes[index][1] <= time:
        queue.append(processes[index])
        index += 1

    while completed < n:
        if not queue:
            time = processes[index][1]
            while index < n and processes[index][1] <= time:
                queue.append(processes[index])
                index += 1

        # Start of round: calculate TQ for this cycle
        rbt_list = [remaining[p[0]] for p in list(queue)]
        if not rbt_list:
            tq = 1
        else:
            avg_bt = _mean(rbt_list)
            min_bt = min(rbt_list)
            tq = max(1, int(math.sqrt(avg_bt * min_bt)))

        k = len(queue)
        
        # Execute k processes for this round
        for _ in range(k):
            current = queue.popleft()
            name = current[0]
            
            # The paper's termination rule: if P(RBT) <= 1TQ *after* running for 1TQ
            # mathematically means if initial RBT <= 2 * TQ, it finishes in one go.
            if remaining[name] <= 2 * tq:
                run_time = remaining[name]
            else:
                run_time = tq
                
            time += run_time
            remaining[name] -= run_time
            
            # Load arrivals during execution
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

    total_wait = sum(completion[p[0]] - p[1] - p[2] for p in processes)
    total_tat = sum(completion[p[0]] - p[1] for p in processes)
    return {"AWT": total_wait / n, "ATT": total_tat / n, "CS": context_switches}


def run_RR(processes):
    """Classic Round Robin logic with fixed time quantum (base TQ)."""
    processes = [[p[0], float(p[1]), float(p[2])] for p in processes]
    processes.sort(key=lambda x: x[1])
    n = len(processes)
    burst_list = [p[2] for p in processes]
    tq_base = (_mean(burst_list) + _median(burst_list)) / 2
    remaining = {p[0]: p[2] for p in processes}
    completion = {p[0]: 0 for p in processes}
    acc_cpu = {p[0]: 0 for p in processes}
    acc_wait = {p[0]: 0 for p in processes}
    last_end = {p[0]: p[1] for p in processes}
    time, completed, index, context_switches = 0, 0, 0, 0
    queue = deque()

    while completed < n:
        while index < n and processes[index][1] <= time:
            queue.append(processes[index])
            index += 1
        if not queue:
            time += 1
            continue
        current = queue.popleft()
        name = current[0]
        acc_wait[name] += time - last_end[name]
        run_time = min(tq_base, remaining[name])
        time += run_time
        acc_cpu[name] += run_time
        remaining[name] -= run_time
        last_end[name] = time
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

    total_wait = sum(completion[p[0]] - p[1] - p[2] for p in processes)
    total_tat = sum(completion[p[0]] - p[1] for p in processes)
    return {"AWT": total_wait / n, "ATT": total_tat / n, "CS": context_switches}


ALGORITHM_REGISTRY = {
    "MMMRR": run_MMMRR,
    "ADRR": run_ADRR,
    "EED-RR": run_EED_RR,
    "ElvHLVQRR": run_ElvHLVQRR,
    "RR": run_RR,
}

# EED-RR: Efficiency-Enhanced Dynamic Round Robin Scheduling

EED-RR (**Efficiency-Enhanced Dynamic Round Robin Scheduling With Jain's Index and Deficit Based Elastic Time Quantum**) is an advanced CPU scheduling algorithm designed to improve upon standard Round Robin by introducing a fairness-regulated, dynamically adapting Time Quantum (TQ).

## Core Concept
Standard Round Robin (RR) scheduling uses a static Time Quantum, which can lead to high Context Switches (if TQ is too small) or poor response times for short processes (if TQ is too large). Furthermore, RR often fails to account for the varying burst characteristics of a mixed workload, leading to starvation of longer processes or unfairness in overall execution time.

**EED-RR** tackles this by dynamically stretching the Time Quantum for processes that are being starved, while ensuring that short processes are not unduly penalized. 

It achieves this using three main components:
1. **Statistical Base TQ**: A baseline Time Quantum calculated from the mean and median of process burst times.
2. **Jain's Fairness Index (JFI)**: A global metric recalculated instantaneously to measure how fairly the CPU is being distributed among all processes based on their efficiency ratio ($x_i = \text{CPU} / (\text{CPU} + \text{Wait})$).
3. **Deficit ($\beta$)**: A per-process starvation multiplier.

## How it works
On every cycle, EED-RR calculates the global Jain's Fairness Index. If the system is perfectly fair, JFI approaches `1.0`. If it's unfair, JFI drops.
When a process is selected from the ready queue, EED-RR checks its deficit ($\beta$). If the process is starved compared to the system average, it is assigned an **Elastic Time Quantum**:

```python
elastic_tq = tq_base * (1 + (1 - JFI) * beta * scaling_factor)
```

- **`(1 - JFI)`**: Acts as an "unfairness" booster. The more unfair the system, the larger this value.
- **`beta`**: Ensures only processes that actually need the extra time (starved processes) get the boost.
- **`scaling_factor`**: A tunable parameter (default `1.5`) that amplifies the elasticity.

This creates a closed-loop system where unfairness automatically triggers a scheduling correction, drastically reducing Average Waiting Time (AWT) and Average Turnaround Time (ATT) without sacrificing fairness.

## Repository Contents

### Main Algorithm Files
* **`EED_RR.py`**: The standard implementation of the Efficiency-Enhanced Dynamic Round Robin algorithm.
* **`EED_RR_Ablation.py`**: A modular version of the algorithm built specifically for ablation studies. It allows you to toggle individual features (Base, +JFI, +Deficit, Full) to evaluate their distinct impact.

### Benchmarks and Baselines
To validate EED-RR, this repository includes several state-of-the-art RR variants for comparison:
* **`ADRR.py`**: Adaptive Dynamic Round Robin.
* **`ElvHLVQRR.py`**: Enhanced Low Variance High Low Variance Quantum Round Robin.
* **`Median_average.py` (MMMRR)**: Mean-Median Modulo Round Robin.
* **`scheduler_runners.py`**: High-performance runners for all included algorithms, optimized for evaluating over massive datasets (10,000+ processes).

### Data and Evaluation
* **`cpu_scheduling_benchmark.ipynb`**: A comprehensive Jupyter Notebook that runs the full evaluation pipeline. It splits the synthetic workload into partitions, evaluates all baseline algorithms against EED-RR, performs statistical significance tests (Wilcoxon signed-rank), computes effect sizes (Cohen's d), and generates heatmaps and bar charts.
* **`generate_process_data.py`**: Script to generate synthetic scheduling datasets with realistic means and standard deviations for arrival and burst times.
* **`process_data.csv`** & **`scheduling_data.csv`**: The datasets containing the processes to be simulated.

## Getting Started
To test the core algorithm directly:
```bash
python EED_RR.py
```
*(Enter the number of processes, followed by their Arrival and Burst times)*

To run the large-scale benchmark and generate performance charts:
Open and execute all cells in `cpu_scheduling_benchmark.ipynb`. This will evaluate all algorithms and output comparison graphs demonstrating EED-RR's performance metrics (AWT, ATT, Context Switches, JFI).

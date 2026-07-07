# EED-RR: Efficiency-Enhanced Dynamic Round Robin Scheduling

EED-RR (Efficiency-Enhanced Dynamic Round Robin Scheduling with Jain’s Index and Deficit-Based Elastic Time Quantum) is an advanced CPU scheduling algorithm designed to address the limitations of traditional Round Robin (RR). It introduces a fairness-aware, dynamically adaptive Time Quantum to improve overall scheduling efficiency.


## Overview

Traditional Round Robin uses a fixed Time Quantum, which often leads to:

* High context switching overhead when the quantum is too small
* Poor responsiveness for short processes when the quantum is too large
* Lack of fairness in mixed workloads

EED-RR overcomes these issues by dynamically adjusting the Time Quantum based on system fairness and process-level starvation.



## Core Components

EED-RR is built on three key ideas:

### 1. Statistical Base Time Quantum

A baseline Time Quantum is computed using statistical properties of burst times (mean and median), providing a balanced starting point.

### 2. Jain’s Fairness Index (JFI)

A global fairness metric that evaluates how evenly CPU time is distributed:

x_i = CPU / (CPU + Wait)

* JFI approaches 1.0 → highly fair system
* Lower JFI → imbalance in scheduling

### 3. Deficit (β)

A per-process starvation factor that tracks how much a process is lagging behind others.



## Algorithm Mechanism

At every scheduling cycle:

1. The global Jain’s Fairness Index is recalculated
2. The scheduler selects the next process
3. If the process is starved, it receives an adjusted (elastic) Time Quantum

Elastic Time Quantum is computed as:

```python
elastic_tq = tq_base * (1 + (1 - JFI) * beta * scaling_factor)
```

Where:

* (1 - JFI): measures system unfairness
* beta: identifies starved processes
* scaling_factor: controls the strength of adjustment (default = 1.5)

This creates a feedback-driven system where unfairness automatically triggers correction, improving:

* Average Waiting Time (AWT)
* Average Turnaround Time (ATT)
* Overall fairness



## Repository Structure

### Main Algorithm

* `EED_RR.py`
  Standard implementation of the EED-RR algorithm

* `EED_RR_Ablation.py`
  Modular version for ablation studies (Base, +JFI, +Deficit, Full)


### Baselines and Comparisons

* `ADRR.py`
  Adaptive Dynamic Round Robin

* `ElvHLVQRR.py`
  Enhanced Low Variance High-Low Variance Quantum RR

* `Median_average.py` (MMMRR)
  Mean-Median Modulo Round Robin

* `scheduler_runners.py`
  Optimized runners for large-scale evaluation (10,000+ processes)

---

### Data and Evaluation

* `cpu_scheduling_benchmark.ipynb`
  Complete evaluation pipeline including:

  * Dataset partitioning
  * Algorithm comparison
  * Statistical tests (Wilcoxon signed-rank)
  * Effect size calculation (Cohen’s d)
  * Visualization (heatmaps, bar charts)

* `generate_process_data.py`
  Synthetic dataset generator with realistic distributions

* `process_data.csv`, `scheduling_data.csv`
  Benchmark datasets

---

## Getting Started

Run the core algorithm interactively:

```bash
python EED_RR.py
```

You will be prompted to input process arrival and burst times.

---

## Run the Benchmark

Execute the full large-scale evaluation in a few steps:

### 1. Clone the Repository

```bash
git clone https://github.com/Md-Pranto/Research_Resources
cd Research_Resources
```

### 2. Open the Notebook

Launch:

```bash
cpu_scheduling_benchmark.ipynb
```

### 3. Execute All Cells

Run all cells to:

* Perform large-scale simulation (10,000 processes)
* Compare EED-RR with multiple RR variants
* Generate performance visualizations

---

## Output

The benchmark produces comparative charts and metrics including:

* Average Waiting Time (AWT)
* Average Turnaround Time (ATT)
* Context Switches
* Jain’s Fairness Index (JFI)

These results highlight the efficiency and fairness improvements achieved by EED-RR over existing scheduling algorithms.

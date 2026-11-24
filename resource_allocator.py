
import pandas as pd


def _assign_to_vm(tasks, task_order, num_vms, cpu_capacity, memory_capacity):
    """Greedily assign tasks to the VM with the lowest normalized load."""

    cpu_load = [0.0] * num_vms
    memory_load = [0.0] * num_vms
    assignments = {}

    for task_index in task_order:
        task = tasks.loc[task_index]

        cpu = float(task["CPU_Requirement"])
        memory = float(task["Memory_Requirement"])

        def vm_score(vm):
            cpu_after = (cpu_load[vm] + cpu) / max(cpu_capacity, 1)
            memory_after = (memory_load[vm] + memory) / max(memory_capacity, 1)

            overload = (
                max(0, cpu_after - 1) * 100
                + max(0, memory_after - 1) * 100
            )

            return max(cpu_after, memory_after) + overload

        selected_vm = min(range(num_vms), key=vm_score)

        assignments[task_index] = selected_vm + 1
        cpu_load[selected_vm] += cpu
        memory_load[selected_vm] += memory

    return assignments


def allocate_tasks(
    tasks,
    method="FCFS",
    ga_chromosome=None,
    num_vms=5,
    cpu_capacity=100,
    memory_capacity=8192
):
    """
    Allocate tasks using FCFS, Fuzzy or GA.

    Returns a DataFrame with the original task data and assigned VM.
    """

    if tasks.empty:
        return pd.DataFrame()

    if num_vms < 1:
        raise ValueError("num_vms must be at least 1")

    working = tasks.copy().reset_index(drop=True)
    method = method.upper()

    if method == "FCFS":
        order = list(working.index)
        assignments = _assign_to_vm(
            working, order, num_vms, cpu_capacity, memory_capacity
        )

    elif method == "FUZZY":
        if "Fuzzy_Score" in working.columns:
            order = working.sort_values(
                "Fuzzy_Score", ascending=False
            ).index.tolist()
        else:
            order = list(working.index)

        assignments = _assign_to_vm(
            working, order, num_vms, cpu_capacity, memory_capacity
        )

    elif method == "GA":
        if ga_chromosome is None or len(ga_chromosome) != len(working):
            raise ValueError("A valid GA chromosome is required.")

        assignments = {
            index: int(ga_chromosome[index]) + 1
            for index in range(len(working))
        }

    else:
        raise ValueError("Method must be FCFS, FUZZY or GA.")

    working["VM"] = [
        assignments[index] for index in range(len(working))
    ]

    working["Allocation_Method"] = method

    return working


def get_vm_usage(
    allocation,
    num_vms,
    cpu_capacity=100,
    memory_capacity=8192
):
    """Return CPU and memory usage for every simulated VM."""

    rows = []

    for vm in range(1, num_vms + 1):
        vm_tasks = allocation[allocation["VM"] == vm]

        cpu_used = vm_tasks["CPU_Requirement"].sum()
        memory_used = vm_tasks["Memory_Requirement"].sum()

        rows.append({
            "VM": f"VM {vm}",
            "Tasks": len(vm_tasks),
            "CPU_Used": round(cpu_used, 2),
            "CPU_Capacity": cpu_capacity,
            "CPU_Utilization_%": round(
                (cpu_used / max(cpu_capacity, 1)) * 100, 2
            ),
            "Memory_Used_MB": round(memory_used, 2),
            "Memory_Capacity_MB": memory_capacity,
            "Memory_Utilization_%": round(
                (memory_used / max(memory_capacity, 1)) * 100, 2
            )
        })

    return pd.DataFrame(rows)


def calculate_metrics(allocation, num_vms, cpu_capacity=100, memory_capacity=8192):
    """Calculate summary metrics for one allocation result."""

    if allocation.empty:
        return {
            "Total_Tasks": 0,
            "Allocated_Tasks": 0,
            "Average_CPU_Utilization": 0,
            "Average_Memory_Utilization": 0,
            "Overloaded_VMs": 0
        }

    vm_usage = get_vm_usage(
        allocation, num_vms, cpu_capacity, memory_capacity
    )

    return {
        "Total_Tasks": len(allocation),
        "Allocated_Tasks": allocation["VM"].notna().sum(),
        "Average_CPU_Utilization": round(
            vm_usage["CPU_Utilization_%"].mean(), 2
        ),
        "Average_Memory_Utilization": round(
            vm_usage["Memory_Utilization_%"].mean(), 2
        ),
        "Overloaded_VMs": int(
            (
                (vm_usage["CPU_Utilization_%"] > 100)
                | (vm_usage["Memory_Utilization_%"] > 100)
            ).sum()
        )
    }

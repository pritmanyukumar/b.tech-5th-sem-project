
import os
import time
import getpass
import psutil
import pandas as pd


def get_mac_tasks(number_of_tasks=10):

    current_user = getpass.getuser()
    processes = []

    for proc in psutil.process_iter(
        ["pid", "name", "username"]
    ):
        try:
            info = proc.info

            if info["pid"] == os.getpid():
                continue

            if info["username"] != current_user:
                continue

            # Initialize CPU measurement.
            proc.cpu_percent(interval=None)
            processes.append(proc)

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

   
    time.sleep(0.5)

    task_records = []

    for proc in processes:
        try:
            cpu = proc.cpu_percent(interval=None)
            memory = proc.memory_info().rss / (1024 * 1024)

            task_records.append({
                "Task_ID": f"P-{proc.pid}",
                "Process_Name": proc.name(),
                "PID": proc.pid,
                "CPU_Requirement": max(1, min(100, round(cpu))),
                "Memory_Requirement": max(1, round(memory)),
                "Waiting_Time": 0,
                "Task_Priority": max(1, min(10, round(cpu / 10) + 1)),
                "Burst_Time": 1,
                "Actual_CPU_Percent": round(cpu, 2),
                "Actual_Memory_MB": round(memory, 2)
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

   
    task_records.sort(
        key=lambda x: x["Actual_CPU_Percent"],
        reverse=True
    )

    return pd.DataFrame(task_records)

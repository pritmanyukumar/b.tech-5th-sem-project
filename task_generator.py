import random
import pandas as pd


def generate_tasks(num_tasks=10):

    tasks = []

    for i in range(1, num_tasks + 1):

        task = {
            "Task_ID": f"T{i}",
            "CPU_Requirement": random.randint(10, 80),
            "Memory_Requirement": random.randint(500, 4000),
            "Waiting_Time": random.randint(1, 30),
            "Task_Priority": random.randint(1, 10),
            "Burst_Time": random.randint(2, 20)
        }

        tasks.append(task)

    return pd.DataFrame(tasks)


if __name__ == "__main__":

    df = generate_tasks(10)

    print("\nGENERATED TASKS")
    print(df.to_string(index=False))

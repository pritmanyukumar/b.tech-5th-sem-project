
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl



cpu = ctrl.Antecedent(np.arange(0, 101, 1), 'cpu')
memory = ctrl.Antecedent(np.arange(0, 4001, 1), 'memory')
waiting = ctrl.Antecedent(np.arange(0, 31, 1), 'waiting')
task_priority = ctrl.Antecedent(
    np.arange(1, 11, 1), 'task_priority'
)


priority_output = ctrl.Consequent(
    np.arange(0, 101, 1), 'priority_output'
)



cpu['low'] = fuzz.trimf(cpu.universe, [0, 0, 50])
cpu['medium'] = fuzz.trimf(cpu.universe, [20, 50, 80])
cpu['high'] = fuzz.trimf(cpu.universe, [50, 100, 100])

# Memory
memory['low'] = fuzz.trimf(memory.universe, [0, 0, 2000])
memory['medium'] = fuzz.trimf(memory.universe, [1000, 2000, 3000])
memory['high'] = fuzz.trimf(memory.universe, [2000, 4000, 4000])

# Waiting time
waiting['low'] = fuzz.trimf(waiting.universe, [0, 0, 15])
waiting['medium'] = fuzz.trimf(waiting.universe, [5, 15, 25])
waiting['high'] = fuzz.trimf(waiting.universe, [15, 30, 30])

# Task priority
task_priority['low'] = fuzz.trimf(
    task_priority.universe, [1, 1, 5]
)
task_priority['medium'] = fuzz.trimf(
    task_priority.universe, [3, 5, 8]
)
task_priority['high'] = fuzz.trimf(
    task_priority.universe, [6, 10, 10]
)

# Output priority
priority_output['low'] = fuzz.trimf(
    priority_output.universe, [0, 0, 40]
)
priority_output['medium'] = fuzz.trimf(
    priority_output.universe, [20, 50, 75]
)
priority_output['high'] = fuzz.trimf(
    priority_output.universe, [50, 75, 90]
)
priority_output['very_high'] = fuzz.trimf(
    priority_output.universe, [75, 100, 100]
)


# 4. Fuzzy IF-THEN rules

rule1 = ctrl.Rule(
    (cpu['high'] & waiting['high']) |
    (memory['high'] & waiting['high']),
    priority_output['very_high']
)

rule2 = ctrl.Rule(
    task_priority['high'] & waiting['high'],
    priority_output['very_high']
)

rule3 = ctrl.Rule(
    waiting['high'],
    priority_output['high']
)

rule4 = ctrl.Rule(
    task_priority['high'],
    priority_output['high']
)

rule5 = ctrl.Rule(
    cpu['medium'] & memory['medium'],
    priority_output['medium']
)

rule6 = ctrl.Rule(
    waiting['medium'],
    priority_output['medium']
)

rule7 = ctrl.Rule(
    cpu['low'] & memory['low'] &
    waiting['low'] & task_priority['low'],
    priority_output['low']
)

rule8 = ctrl.Rule(
    waiting['low'] & task_priority['low'],
    priority_output['low']
)

rule9 = ctrl.Rule(
    (cpu['high'] | memory['high']) & waiting['low'],
    priority_output['medium']
)

# NEW RULES: Cover missing combinations

rule10 = ctrl.Rule(
    waiting['low'] & task_priority['medium'],
    priority_output['medium']
)

rule11 = ctrl.Rule(
    waiting['low'] & task_priority['high'],
    priority_output['high']
)


# 5. Create fuzzy control system
priority_control = ctrl.ControlSystem([
    rule1, rule2, rule3, rule4, rule5,
    rule6, rule7, rule8, rule9,
    rule10, rule11
])


# 6. Calculate task priority
def calculate_task_priority(
    cpu_value, memory_value,
    waiting_value, task_priority_value
):

    # Keep inputs within valid ranges
    cpu_value = np.clip(cpu_value, 0, 100)
    memory_value = np.clip(memory_value, 0, 4000)
    waiting_value = np.clip(waiting_value, 0, 30)
    task_priority_value = np.clip(
        task_priority_value, 1, 10
    )

    simulation = ctrl.ControlSystemSimulation(
        priority_control
    )

    simulation.input['cpu'] = float(cpu_value)
    simulation.input['memory'] = float(memory_value)
    simulation.input['waiting'] = float(waiting_value)
    simulation.input['task_priority'] = float(
        task_priority_value
    )

    simulation.compute()

    if 'priority_output' not in simulation.output:
        raise ValueError(
            "Fuzzy system could not calculate priority."
        )

    score = simulation.output['priority_output']

    if score < 30:
        label = "Low"
    elif score < 55:
        label = "Medium"
    elif score < 80:
        label = "High"
    else:
        label = "Very High"

    return round(score, 2), label


# 7. Test fuzzy logic
if __name__ == "__main__":

    score, label = calculate_task_priority(
        80, 3500, 25, 9
    )

    print("\nFUZZY LOGIC RESULT")
    print("------------------")
    print("Priority Score:", score)
    print("Priority Level:", label)

    # Test different combinations
    test_cases = [
        (10, 500, 2, 2),
        (40, 1500, 10, 5),
        (80, 3500, 25, 9),
        (20, 1000, 5, 7)
    ]

    print("\nMULTIPLE TEST RESULTS")

    for values in test_cases:
        score, label = calculate_task_priority(*values)
        print(values, "=>", score, label)

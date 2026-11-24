
import random
import numpy as np

POPULATION_SIZE = 20
GENERATIONS = 15
MUTATION_RATE = 0.08


def calculate_fitness(
    chromosome,
    cpu_requirements,
    memory_requirements,
    num_vms,
    cpu_capacity,
    memory_capacity
):
    cpu_load = np.bincount(
        chromosome,
        weights=cpu_requirements,
        minlength=num_vms
    )

    memory_load = np.bincount(
        chromosome,
        weights=memory_requirements,
        minlength=num_vms
    )

    cpu_overload = np.maximum(0, cpu_load - cpu_capacity)
    memory_overload = np.maximum(0, memory_load - memory_capacity)

    penalty = np.sum(cpu_overload) * 10
    penalty += np.sum(memory_overload) * 0.05

    cpu_util = cpu_load / max(cpu_capacity, 1)
    memory_util = memory_load / max(memory_capacity, 1)

    balance_penalty = np.sum(np.abs(cpu_util - memory_util))

    return float(1000 - penalty - balance_penalty * 10)


def crossover(parent1, parent2):
    if len(parent1) < 2:
        return parent1.copy()

    point = random.randint(1, len(parent1) - 1)

    return np.concatenate([
        parent1[:point],
        parent2[point:]
    ])


def mutate(chromosome, num_vms, mutation_rate=MUTATION_RATE):
    child = chromosome.copy()

    mask = np.random.random(len(child)) < mutation_rate

    child[mask] = np.random.randint(
        0, num_vms, size=np.sum(mask)
    )

    return child


def genetic_algorithm(
    tasks,
    num_vms=5,
    cpu_capacity=100,
    memory_capacity=8192
):
    if tasks.empty:
        return [], 0.0

    if num_vms < 1:
        raise ValueError("num_vms must be at least 1")

    cpu_requirements = tasks["CPU_Requirement"].to_numpy(dtype=float)
    memory_requirements = tasks["Memory_Requirement"].to_numpy(dtype=float)

    task_count = len(tasks)

    population = [
        np.random.randint(0, num_vms, size=task_count)
        for _ in range(POPULATION_SIZE)
    ]

    best_chromosome = population[0].copy()
    best_fitness = float("-inf")

    for generation in range(GENERATIONS):

        fitness_values = [
            calculate_fitness(
                chromosome,
                cpu_requirements,
                memory_requirements,
                num_vms,
                cpu_capacity,
                memory_capacity
            )
            for chromosome in population
        ]

        ranked_indices = np.argsort(fitness_values)[::-1]

        if fitness_values[ranked_indices[0]] > best_fitness:
            best_fitness = fitness_values[ranked_indices[0]]
            best_chromosome = population[ranked_indices[0]].copy()

        # Keep the two best chromosomes.
        new_population = [
            population[ranked_indices[0]].copy(),
            population[ranked_indices[1]].copy()
        ]

        # Use the better half as parents.
        parent_pool = [
            population[i]
            for i in ranked_indices[:max(2, POPULATION_SIZE // 2)]
        ]

        while len(new_population) < POPULATION_SIZE:
            parent1 = random.choice(parent_pool)
            parent2 = random.choice(parent_pool)

            child = crossover(parent1, parent2)
            child = mutate(child, num_vms)

            new_population.append(child)

        population = new_population

    return best_chromosome.tolist(), round(best_fitness, 4)

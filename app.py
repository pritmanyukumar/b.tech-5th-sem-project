import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import psutil
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# PROJECT MODULES
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULES_PATH = PROJECT_ROOT / "modules"

sys.path.insert(0, str(MODULES_PATH))

from mac_task_monitor import get_mac_tasks
from fuzzy_logic import calculate_task_priority
from genetic_algorithm import genetic_algorithm
from resource_allocator import (
    allocate_tasks,
    get_vm_usage,
    calculate_metrics
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ResourceIQ | Mac Resource Monitor",
    layout="wide"
)

# Automatically refresh every 5 seconds
st_autorefresh(
    interval=5000,
    key="mac_process_auto_refresh"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background: #0b1120;
    color: #e5e7eb;
}

h1, h2, h3 {
    color: #f8fafc !important;
}

.hero {
    padding: 24px;
    border-radius: 16px;
    background: linear-gradient(120deg, #172554, #164e63);
    border: 1px solid #2563eb;
    margin-bottom: 20px;
}

.hero h1 {
    color: white !important;
}

.hero p {
    color: #cbd5e1;
}

[data-testid="stMetric"] {
    background: #111c30;
    border: 1px solid #26364f;
    padding: 15px;
    border-radius: 12px;
}

section[data-testid="stSidebar"] {
    background: #101a2c;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("ResourceIQ")
st.sidebar.caption("Mac Resource Allocation Dashboard")
st.sidebar.divider()

st.sidebar.subheader("Task Settings")

st.sidebar.info(
    "Mac processes are detected automatically. "
    "Task count updates every 5 seconds."
)

st.sidebar.subheader("Simulated VM Settings")

num_vms = st.sidebar.slider(
    "Number of simulated VMs",
    min_value=2,
    max_value=10,
    value=5
)

cpu_capacity = st.sidebar.number_input(
    "CPU capacity per VM (simulation units)",
    min_value=1,
    max_value=1000,
    value=100
)

memory_capacity = st.sidebar.number_input(
    "Memory capacity per VM (MB)",
    min_value=256,
    max_value=100000,
    value=8192,
    step=512
)

st.sidebar.caption(
    "VM capacities are simulation settings, not actual Mac hardware limits."
)

if st.sidebar.button("🔄 Refresh Now", use_container_width=True):
    st.rerun()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("""
<div class="hero">
    <h1> ResourceIQ Dashboard</h1>
    <p>
        Intelligent resource allocation using real Mac process data
    </p>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# AUTOMATIC MAC PROCESS DETECTION
# --------------------------------------------------

with st.spinner("Detecting Mac processes..."):

    # Get ALL accessible processes
    tasks = get_mac_tasks()

    tasks = tasks.reset_index(drop=True)


if tasks.empty:
    st.warning("No accessible Mac processes found.")
    st.stop()


# Display detected count
st.success(
    f"Currently detecting {len(tasks)} accessible Mac processes."
)


# --------------------------------------------------
# FUZZY LOGIC PRIORITY
# --------------------------------------------------

priority_results = tasks.apply(
    lambda row: calculate_task_priority(
        row["CPU_Requirement"],
        row["Memory_Requirement"],
        row["Waiting_Time"],
        row["Task_Priority"]
    ),
    axis=1
)

tasks["Fuzzy_Score"] = [
    result[0] for result in priority_results
]

tasks["Fuzzy_Priority"] = [
    result[1] for result in priority_results
]


# --------------------------------------------------
# GENETIC ALGORITHM
# --------------------------------------------------

with st.spinner("Running Genetic Algorithm..."):

    ga_chromosome, best_fitness = genetic_algorithm(
        tasks,
        num_vms=num_vms,
        cpu_capacity=cpu_capacity,
        memory_capacity=memory_capacity
    )


# --------------------------------------------------
# RESOURCE ALLOCATION
# --------------------------------------------------

fcfs_allocation = allocate_tasks(
    tasks,
    method="FCFS",
    num_vms=num_vms,
    cpu_capacity=cpu_capacity,
    memory_capacity=memory_capacity
)

fuzzy_allocation = allocate_tasks(
    tasks,
    method="FUZZY",
    num_vms=num_vms,
    cpu_capacity=cpu_capacity,
    memory_capacity=memory_capacity
)

ga_allocation = allocate_tasks(
    tasks,
    method="GA",
    ga_chromosome=ga_chromosome,
    num_vms=num_vms,
    cpu_capacity=cpu_capacity,
    memory_capacity=memory_capacity
)


# --------------------------------------------------
# REAL MAC HARDWARE MONITORING
# --------------------------------------------------

st.subheader("Live Mac Hardware")

cpu_percent = psutil.cpu_percent(interval=0.3)
memory = psutil.virtual_memory()
disk = psutil.disk_usage("/")

col1, col2, col3 = st.columns(3)

col1.metric("Mac CPU Usage", f"{cpu_percent:.1f}%")
col2.metric("Mac RAM Usage", f"{memory.percent:.1f}%")
col3.metric("Disk Usage", f"{disk.percent:.1f}%")

st.progress(
    min(cpu_percent / 100, 1.0),
    text="Mac CPU Usage"
)

st.progress(
    min(memory.percent / 100, 1.0),
    text="Mac RAM Usage"
)

st.caption(
    f"Total RAM: {memory.total / (1024 ** 3):.1f} GB | "
    f"Available RAM: {memory.available / (1024 ** 3):.1f} GB | "
    f"Logical CPU cores: {psutil.cpu_count()}"
)


# --------------------------------------------------
# OVERVIEW METRICS
# --------------------------------------------------

st.divider()
st.subheader("Resource Allocation Overview")

m1, m2, m3, m4 = st.columns(4)

m1.metric("Live Mac Processes", len(tasks))

m2.metric("Simulated VMs", num_vms)

m3.metric(
    "High Priority Tasks",
    int((tasks["Fuzzy_Priority"] == "High").sum())
)

m4.metric("GA Best Fitness", f"{best_fitness:.2f}")


# --------------------------------------------------
# DASHBOARD TABS
# --------------------------------------------------

overview_tab, task_tab, vm_tab, performance_tab, download_tab = st.tabs([
    "Overview",
    "Task Details",
    "VM Monitoring",
    "Performance",
    "Download"
])


# --------------------------------------------------
# OVERVIEW TAB
# --------------------------------------------------

with overview_tab:

    st.subheader("Process Priority Distribution")

    priority_counts = (
        tasks["Fuzzy_Priority"]
        .value_counts()
        .reindex(["High", "Medium", "Low"], fill_value=0)
    )

    st.bar_chart(priority_counts)

    st.subheader("CPU Usage by Mac Process")

    cpu_chart = tasks.set_index("Process_Name")[
        "Actual_CPU_Percent"
    ]

    st.bar_chart(cpu_chart)


# --------------------------------------------------
# TASK DETAILS TAB
# --------------------------------------------------

with task_tab:

    st.subheader(" Actual Mac Processes")

    st.caption(
        f"Automatically detected processes: {len(tasks)}"
    )

    st.dataframe(
        tasks[
            [
                "Task_ID",
                "Process_Name",
                "PID",
                "Actual_CPU_Percent",
                "Actual_Memory_MB",
                "Fuzzy_Score",
                "Fuzzy_Priority"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Task Priority Details")

    st.dataframe(
        tasks[
            [
                "Task_ID",
                "Process_Name",
                "CPU_Requirement",
                "Memory_Requirement",
                "Task_Priority",
                "Fuzzy_Priority"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# VM MONITORING TAB
# --------------------------------------------------

with vm_tab:

    st.subheader("Genetic Algorithm VM Allocation")

    vm_usage = get_vm_usage(
        ga_allocation,
        num_vms,
        cpu_capacity,
        memory_capacity
    )

    st.dataframe(
        vm_usage,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("VM CPU Utilization")

    st.bar_chart(
        vm_usage.set_index("VM")["CPU_Utilization_%"]
    )

    st.subheader("VM Memory Utilization")

    st.bar_chart(
        vm_usage.set_index("VM")["Memory_Utilization_%"]
    )

    st.subheader("Process-to-VM Mapping")

    st.dataframe(
        ga_allocation[
            [
                "Task_ID",
                "Process_Name",
                "PID",
                "VM",
                "CPU_Requirement",
                "Memory_Requirement"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    overloaded = vm_usage[
        (vm_usage["CPU_Utilization_%"] > 100)
        | (vm_usage["Memory_Utilization_%"] > 100)
    ]

    if not overloaded.empty:
        st.warning(
            "Some simulated VMs exceed their configured capacity."
        )
    else:
        st.success("No simulated VM capacity violations.")


# --------------------------------------------------
# PERFORMANCE TAB
# --------------------------------------------------

with performance_tab:

    st.subheader("Algorithm Comparison")

    fcfs_metrics = calculate_metrics(
        fcfs_allocation,
        num_vms,
        cpu_capacity,
        memory_capacity
    )

    fuzzy_metrics = calculate_metrics(
        fuzzy_allocation,
        num_vms,
        cpu_capacity,
        memory_capacity
    )

    ga_metrics = calculate_metrics(
        ga_allocation,
        num_vms,
        cpu_capacity,
        memory_capacity
    )

    comparison = pd.DataFrame([
        {"Algorithm": "FCFS", **fcfs_metrics},
        {"Algorithm": "Fuzzy Logic", **fuzzy_metrics},
        {"Algorithm": "Genetic Algorithm", **ga_metrics}
    ])

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Average CPU Utilization")

    st.bar_chart(
        comparison.set_index("Algorithm")[
            "Average_CPU_Utilization"
        ]
    )

    st.subheader("Average Memory Utilization")

    st.bar_chart(
        comparison.set_index("Algorithm")[
            "Average_Memory_Utilization"
        ]
    )


# --------------------------------------------------
# DOWNLOAD TAB
# --------------------------------------------------

with download_tab:

    st.subheader("Download Reports")

    st.download_button(
        "⬇️ Download Mac Process Data",
        data=tasks.to_csv(index=False).encode("utf-8"),
        file_name="resourceiq_mac_processes.csv",
        mime="text/csv"
    )

    st.download_button(
        "⬇️ Download GA Allocation",
        data=ga_allocation.to_csv(index=False).encode("utf-8"),
        file_name="resourceiq_allocation.csv",
        mime="text/csv"
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "ResourceIQ | Real Mac Process Monitoring "
    "+ Simulated Intelligent Resource Allocation"
)

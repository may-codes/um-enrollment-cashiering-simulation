import streamlit as st
import simpy
import random
import statistics
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, time, timedelta

# Set page configuration
st.set_page_config(
    page_title="UM Enrollment Capacity Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Formal Custom Styling (Corporate/Academic Palette)
st.markdown("""
<style>
    /* Global layout adjustments */
    .reportview-container .main .block-container { 
        max-width: 95%; 
        padding-top: 2rem;
    }
    
    /* Main titles and subheaders */
    h1 {
        color: #0f2042;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    h2, h3 {
        color: #2d3748;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 600;
    }
    
    /* Executive Metric Cards */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        border-top: 4px solid #0f2042;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .metric-header { 
        font-size: 13px; 
        color: #718096; 
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600; 
    }
    .metric-value { 
        font-size: 22px; 
        color: #0f2042; 
        font-weight: 700;
        margin-top: 5px;
    }
    .metric-sub {
        font-size: 13px;
        color: #4a5568;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# APP HEADER & TITLE BLOCK (Official Research Identity)
st.title("UM Enrollment Cashiering Simulation Tool")
st.markdown("""
### Discrete Event Simulation of the University of Mindanao (UM) Cashiering System: Determining Optimal Window Capacity for Peak Enrollment Demand

This predictive simulation model analyzes student arrival distributions, queue formations, and transactional 
throughput at the **University of Mindanao (UM) Cashier's Office**. By simulating operational flows under 
stochastic constraints, this decision support tool evaluates counter window capacities to mathematically 
determine optimal staffing levels required to meet peak enrollment demand while minimizing service bottlenecks.
""")

# SIDEBAR PARAMETERS (Interactive Decision Support Controls)
st.sidebar.header("Simulation Configuration")

# Hardcoded Random Seed for reproducibility (Devs can modify here)
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Window Testing Configurations
st.sidebar.subheader("Counter Windows Setup")
min_windows = st.sidebar.slider(
    "Minimum Windows to Test", 1, 20, 3,
    help="The lowest number of cashier windows you want to test. The simulation starts evaluating capacity from this number."
)
max_windows = st.sidebar.slider(
    "Maximum Windows to Test", min_windows, 20, 12,
    help="The highest number of cashier windows you want to test. The system will calculate and compare every option step-by-step between your lowest and highest choices."
)

# Operational Controls
st.sidebar.subheader("Operating Parameters")

# Clock Input Setup for Transaction Window Tracking
start_time_input = st.sidebar.time_input(
    "Transaction Start Time", 
    value=time(8, 0),
    help="The exact time the cashier windows open for the day and students begin arriving at the office (e.g., 08:00 AM)."
)
end_time_input = st.sidebar.time_input(
    "Transaction End Time", 
    value=time(17, 0),
    help="The official time the office doors close for the day (e.g., 05:00 PM). Any student still in line after this time must still be processed, resulting in staff overtime."
)

early_arrivals_enabled = st.sidebar.checkbox(
    "Allow Early Student Arrivals",
    value=True,
    help="When enabled (default), some students will arrive 5-30 minutes before opening and queue up early, creating a backlog when doors open. When disabled, arrivals only begin when doors open."
)

# Calculate dynamic minutes from clock settings for the underlying SimPy backend
dt_start = datetime.combine(datetime.today(), start_time_input)
dt_end = datetime.combine(datetime.today(), end_time_input)
if dt_end <= dt_start:
    dt_end += timedelta(days=1)  # Accounts for spillover safely

DAY_DURATION = int((dt_end - dt_start).total_seconds() / 60)

# Real-time informational message under the time pickers
st.sidebar.info(f"Total calculated operational window: {DAY_DURATION} minutes ({DAY_DURATION/60:.1f} hours)")

# Initialize or update random daily volumes in session state based on transaction time
# Model: ~65-72% of daily cap are early birds (arrive before 8 AM) ≈ 900-1100 students.
# During-hours (8 AM onwards) adds 400-600 more at 1/min before ticket window cuts off.
# Total cap per day: 1400-1700 — well under 2000, matching real UM ticket cutoff practice.
scale = DAY_DURATION / 540.0
if "random_daily_students" not in st.session_state or st.session_state.get("prev_duration") != DAY_DURATION:
    sys_rand = random.SystemRandom()
    st.session_state.random_daily_students = {
        1: int(sys_rand.randint(1400, 1500) * scale),   # Day 1: ~910-1080 early birds + 490-420 during hours
        2: int(sys_rand.randint(1450, 1550) * scale),   # Day 2: ~940-1116 early birds + 510-434 during hours
        3: int(sys_rand.randint(1500, 1600) * scale),   # Day 3: ~975-1152 early birds + 525-448 during hours
        4: int(sys_rand.randint(1550, 1650) * scale),   # Day 4: ~1008-1188 early birds + 542-462 during hours
        5: int(sys_rand.randint(1600, 1700) * scale),   # Day 5: ~1040-1224 early birds + 560-476 during hours
    }
    st.session_state.prev_duration = DAY_DURATION

# Student Volume Input Setup
st.sidebar.subheader("Daily Student Arrivals")

customize_arrivals = st.sidebar.checkbox(
    "Customize Daily Volumes Manually",
    value=False,
    help="Enable this to manually specify the number of student arrivals for each of the 5 days instead of using scaled random volumes."
)

if customize_arrivals:
    with st.sidebar.expander("Customize Volume Per Day", expanded=True):
        day1_vol = st.number_input("Day 1 Volume", min_value=10, max_value=5000, value=st.session_state.random_daily_students[1], step=50, help="Total number of students arriving to pay on the first day of the peak season.")
        day2_vol = st.number_input("Day 2 Volume", min_value=10, max_value=5000, value=st.session_state.random_daily_students[2], step=50, help="Total number of students arriving to pay on the second day of the peak season.")
        day3_vol = st.number_input("Day 3 Volume", min_value=10, max_value=5000, value=st.session_state.random_daily_students[3], step=50, help="Total number of students arriving to pay on the third day of the peak season.")
        day4_vol = st.number_input("Day 4 Volume", min_value=10, max_value=5000, value=st.session_state.random_daily_students[4], step=50, help="Total number of students arriving to pay on the fourth day of the peak season.")
        day5_vol = st.number_input("Day 5 Volume", min_value=10, max_value=5000, value=st.session_state.random_daily_students[5], step=50, help="Total number of students arriving to pay on the fifth day (the absolute heaviest peak day).")
    daily_students = {
        1: day1_vol,
        2: day2_vol,
        3: day3_vol,
        4: day4_vol,
        5: day5_vol
    }
else:
    st.sidebar.info(
        f"**Active Random Volumes:**\n"
        f"- Day 1: {st.session_state.random_daily_students[1]}\n"
        f"- Day 2: {st.session_state.random_daily_students[2]}\n"
        f"- Day 3: {st.session_state.random_daily_students[3]}\n"
        f"- Day 4: {st.session_state.random_daily_students[4]}\n"
        f"- Day 5: {st.session_state.random_daily_students[5]}"
    )
    if st.sidebar.button("Regenerate Random Volumes"):
        if "random_daily_students" in st.session_state:
            del st.session_state["random_daily_students"]
        st.rerun()
        
    daily_students = st.session_state.random_daily_students

# Student Profile Percentage Split Section
st.sidebar.subheader("Student Category Mix")
with st.sidebar.expander("Set Category Percentages", expanded=True):
    old_student_percent = st.number_input(
        "Old Student %", min_value=0, max_value=100, value=70, step=5,
        help="What percentage of the daily crowd consists of Old/Returning students. These transactions are usually faster."
    )
    new_student_percent = st.number_input(
        "New Student %", min_value=0, max_value=100, value=30, step=5,
        help="What percentage of the daily crowd consists of New/Freshmen students. These transactions usually take longer because of profile registration."
    )

# Validate split parameters total 100%
total_percentage = old_student_percent + new_student_percent
if total_percentage != 100:
    st.sidebar.error(f"Validation Error: Percentages must sum to exactly 100%. Current sum: {total_percentage}%")

# Dynamic Service Duration Input Sliders
st.sidebar.subheader("Counter Transaction Durations")
with st.sidebar.expander("Adjust Time Ranges (Mins)", expanded=True):
    old_range = st.slider(
        "Old Student Time Range", 
        min_value=1, max_value=15, value=(3, 5),
        help="Set the minimum and maximum number of minutes an Old Student spends at the cashier counter window to complete their transaction."
    )
    new_range = st.slider(
        "New Student Time Range", 
        min_value=1, max_value=20, value=(5, 11),
        help="Set the minimum and maximum number of minutes a New Student spends at the cashier counter window to complete their transaction."
    )

# Backend Dynamic Translation: Map chosen slider values into target statistical curves
old_mean = sum(old_range) / 2.0
old_std = max(0.5, (old_range[1] - old_range[0]) / 2.0)

new_low, new_high = max(0.5, new_range[0]), max(1.0, new_range[1])
new_mean = (new_low + new_high) / 2.0
new_var = ((new_high - new_low) / 4.0) ** 2
new_sigma = np.sqrt(np.log(1 + (new_var / (new_mean ** 2))))
new_mu = np.log(new_mean) - (new_sigma ** 2) / 2.0

# GLOBAL STORAGE VARIABLES FOR SIMULATION MONITORING

wait_times = []
service_times = []
students_arrived = 0
students_served = 0
students_balked = 0
queue_lengths = []


# CASHIERING DES SIMULATION ENGINE (SimPy)

class CashieringSystem:
    def __init__(self, env, windows):
        self.env = env
        self.cashier = simpy.Resource(env, capacity=windows)

    def process_payment(self, student_type):
        global service_times
        if student_type == "old":
            service_time = max(old_range[0], random.normalvariate(old_mean, old_std))
        else:
            service_time = max(new_range[0], random.lognormvariate(new_mu, new_sigma))
        
        service_times.append(service_time)
        yield self.env.timeout(service_time)

def student_process(env, name, system, student_type, arrival_time=None):
    """
    Models a single student's journey through the cashiering system.
    - Pre-queue students (arrival_time=0): arrived before 8 AM at 1/min intervals.
      They sleep until t=0 (office opening) before joining the cashier queue.
    - During-hours students (arrival_time=None): arrive after 8 AM, record time then
      take a short slip-machine delay before queuing.
    """
    global wait_times, students_arrived, students_served, students_balked, queue_lengths
    students_arrived += 1

    if arrival_time is None:
        # Student arriving during office hours — record when they join
        arrival_time = env.now
        # Short queue number slip machine delay
        yield env.timeout(random.uniform(0.5, 1.0))
    else:
        # Pre-queue student: wait until the office opens at t=0 if not there yet
        if env.now < 0:
            yield env.timeout(-env.now)  # sleep exactly until 8 AM

    current_queue = len(system.cashier.queue)
    queue_lengths.append(current_queue)

    # Rare balking: ~5% of students give up and throw away their ticket
    if random.random() < 0.05:
        students_balked += 1
        return

    # Enter main queue and wait for an available cashier window
    with system.cashier.request() as request:
        yield request
        wait = env.now - arrival_time
        wait_times.append(wait)
        yield env.process(system.process_payment(student_type))
        students_served += 1

def arrival_generator(env, system, total_students, official_cutoff, early_arrivals_enabled, pre_queue_count):
    """
    Simulates the real UM cashiering arrival pattern:
      Phase 1 — Pre-opening (t < 0): students arrive 1-per-minute before 8 AM.
                 Each student sleeps until t=0 before joining the cashier queue.
                 The env clock starts at -pre_queue_count so there are exactly enough
                 minutes for all early birds to arrive before the office opens.
      Phase 2 — During hours (t=0 to official_cutoff): 1 student per minute continues
                 arriving until the ticket cap (total_students) is hit.
      After cap: ticket window closed; env.run() finishes all remaining service (overtime).
    """
    student_id = 0

    # Phase 1: Pre-opening arrivals — 1 student per minute leading up to 8 AM
    if early_arrivals_enabled and pre_queue_count > 0:
        for i in range(pre_queue_count):
            yield env.timeout(1.0)  # 1-minute interarrival (same as during-hours)
            student_type = random.choices(["old", "new"], weights=[old_student_percent, new_student_percent])[0]
            # arrival_time=0: wait is measured from 8 AM (office opening), not from physical arrival
            env.process(student_process(env, f"PreQueue-{student_id}", system, student_type, arrival_time=0))
            student_id += 1
        # env.now is now exactly 0 (8 AM) — all early birds have arrived and are sleeping until t=0

    # Phase 2: During-hours arrivals — exactly 1 student per minute until ticket cap
    while env.now < official_cutoff and student_id < total_students:
        yield env.timeout(1.0)  # fixed 1-minute interarrival
        student_type = random.choices(["old", "new"], weights=[old_student_percent, new_student_percent])[0]
        env.process(student_process(env, f"Student-{student_id}", system, student_type))
        student_id += 1
    # After loop exits: ticket window is closed, but env.run() continues until all queued students are served


def run_simulation(window_count, early_arrivals_enabled):
    daily_results = []
    
    for day, total_students in daily_students.items():
        global wait_times, service_times, students_arrived, students_served, students_balked, queue_lengths
        
        # Reset storage matrices per day execution
        wait_times, service_times, queue_lengths = [], [], []
        students_arrived, students_served, students_balked = 0, 0, 0

        # Determine how many students arrive BEFORE 8 AM (early birds, 1/min)
        # The env clock will start exactly -pre_queue_count minutes before 8 AM
        if early_arrivals_enabled:
            pre_queue_ratio = random.uniform(0.65, 0.72)
            pre_queue_count = min(int(total_students * pre_queue_ratio), total_students)
        else:
            pre_queue_count = 0

        # Start simulation clock at -(pre_queue_count) so early birds arrive 1/min up to t=0
        env = simpy.Environment(initial_time=-pre_queue_count)
        system = CashieringSystem(env, window_count)
        
        env.process(arrival_generator(env, system, total_students, DAY_DURATION, early_arrivals_enabled, pre_queue_count))
        env.run()
        
        end_time = env.now  # positive: minutes after 8 AM when last student was served
        overtime_minutes = max(0.0, end_time - DAY_DURATION)
        
        avg_wait = float(statistics.mean(wait_times)) if wait_times else 0.0
        max_wait = float(max(wait_times)) if wait_times else 0.0
        
        total_service = sum(service_times)
        # Cashier works from t=0 (office open) to t=end_time — don't count pre-opening time
        cashier_available_minutes = window_count * max(end_time, 0)
        utilization = (total_service / cashier_available_minutes) * 100 if cashier_available_minutes > 0 else 0.0
        avg_service = float(statistics.mean(service_times)) if service_times else 0.0
        
        daily_results.append({
            "day": day,
            "incoming": students_arrived,  # actual arrivals counted during simulation
            "served": students_served,
            "balked": students_balked,
            "avg_wait": avg_wait,
            "max_wait": max_wait,
            "utilization": utilization,
            "overtime_hours": overtime_minutes / 60.0,
            "max_queue": max(queue_lengths) if queue_lengths else 0,
            "avg_service": avg_service
        })
        
    return daily_results

# Execute iterative analysis loops
window_analysis = {}
for windows in range(min_windows, max_windows + 1):
    window_analysis[windows] = run_simulation(windows, early_arrivals_enabled)

# Flatten datasets to construct tabular DataFrames
flat_data = []
for win, days_list in window_analysis.items():
    for d_res in days_list:
        row = {"Tested Windows": win}
        row.update(d_res)
        flat_data.append(row)

df_all = pd.DataFrame(flat_data)

# WEBAPP LAYOUT AND VISUALIZATION

# Navigation Tab Infrastructure
tab1, tab2, tab3 = st.tabs(["Recommendation Center", "Detailed Performance Charts", "Comprehensive Data Tables"])

with tab1:
    st.subheader("Data-Driven Capacity Recommendation")
    
    # Establish customizable targets
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        target_wait = st.slider(
            "Target Maximum Average Wait Time (Minutes)", 15, 60, 30,
            help="Your administrative goal for student satisfaction. The dashboard will find the lowest number of windows needed to keep the average queue moving under this timeframe."
        )
    with col_t2:
        max_allowed_overtime = st.slider(
            "Maximum Allowable Staff Overtime (Hours)", 0.0, 5.0, 0.5, step=0.5,
            help="Your administrative limit for cashier overtime. The dashboard will disqualify any window setup that forces staff to stay beyond this point after doors officially close."
        )
        
    # Evaluate configuration compliance
    recommended_windows = None
    for windows in sorted(window_analysis.keys()):
        compliant = True
        for day_res in window_analysis[windows]:
            if day_res["avg_wait"] > target_wait or day_res["overtime_hours"] > max_allowed_overtime:
                compliant = False
                break
        if compliant:
            recommended_windows = windows
            break
            
    if recommended_windows:
        st.success(f"**Recommendation Match:** Open **{recommended_windows} Cashier Windows** to successfully maintain standard service thresholds across all 5 evaluated peak periods.")
    else:
        st.error("**Capacity Constraint Warning:** No tested window configurations met both constraints simultaneously during peak volume hours. Review targets or expand the tested scope.")

    # Summary scorecard section
    st.markdown("---")
    st.subheader("Peak Volume Allocation Matrix (Day 5 Analytics)")
    
    sample_windows = [min_windows, min(min_windows+2, max_windows), min(min_windows+5, max_windows), max_windows]
    sample_windows = list(set(sample_windows))
    sample_windows.sort()
    
    cols = st.columns(len(sample_windows))
    for idx, w in enumerate(sample_windows):
        d5_data = df_all[(df_all["Tested Windows"] == w) & (df_all["day"] == 5)].iloc[0]
        with cols[idx]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-header">{w} Windows Active</div>
                <div class="metric-value">Served: {d5_data['served']}</div>
                <div class="metric-sub">
                    Balked Count: <b>{d5_data['balked']}</b><br>
                    Mean Wait: <b>{d5_data['avg_wait']:.1f} mins</b><br>
                    Overtime Required: <b>{d5_data['overtime_hours']:.2f} hrs</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    view_type = st.radio(
        "Choose Analysis Perspective:",
        ["Trend Over Peak Days (Single Metric)", "Daily Detailed Performance Metrics (All 5 Key Metrics)"],
        horizontal=True,
        help="Select 'Trend Over Peak Days' to see how one metric changes across all days, or 'Daily Detailed Performance Metrics' to view all 5 KPIs for a specific day."
    )
    
    if view_type == "Trend Over Peak Days (Single Metric)":
        st.subheader("Operational Optimization Curves")
        
        metric_choice = st.selectbox(
            "Select Performance Optimization Metric to Plot:",
            ["Average Wait Time (Minutes)", "Staff Overtime (Hours)", "Students Lost (Balking Count)", "Cashier Resource Utilization (%)"],
            help="Choose an operational metric to visually see how different window layouts behave over the 5 peak days."
        )
        
        # Map selection keys to dataset column targets
        metric_map = {
            "Average Wait Time (Minutes)": "avg_wait",
            "Staff Overtime (Hours)": "overtime_hours",
            "Students Lost (Balking Count)": "balked",
            "Cashier Resource Utilization (%)": "utilization"
        }
        db_col = metric_map[metric_choice]
        
        # Matplotlib Configuration
        fig, ax = plt.subplots(figsize=(11, 4.5))
        for win in sorted(window_analysis.keys()):
            df_subset = df_all[df_all["Tested Windows"] == win]
            ax.plot(df_subset["day"], df_subset[db_col], marker='o', linewidth=1.5, markersize=5, label=f"{win} Windows")
            
        ax.set_xlabel("Peak Enrollment Interval", fontsize=10, color="#2d3748")
        ax.set_ylabel(metric_choice, fontsize=10, color="#2d3748")
        ax.set_title(f"Dynamic Operations Trajectory: {metric_choice}", fontsize=11, fontweight='bold', color="#0f2042", pad=15)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"])
        ax.grid(True, linestyle=':', alpha=0.5, color="#cbd5e0")
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0')
        
        # Style adjustment for plotting area boundaries
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e0')
        ax.spines['bottom'].set_color('#cbd5e0')
        
        st.pyplot(fig)
    else:
        st.subheader("Daily Detailed Metrics across Window Counts")
        selected_day = st.selectbox(
            "Select Day to Analyze:",
            ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
            help="Choose a simulated day to inspect all five key performance indicators across the tested window capacities."
        )
        day_map = {"Day 1": 1, "Day 2": 2, "Day 3": 3, "Day 4": 4, "Day 5": 5}
        day_val = day_map[selected_day]
        
        df_day = df_all[df_all["day"] == day_val].sort_values("Tested Windows")
        
        # Define 5 subplots in a 2x3 grid
        fig, axes = plt.subplots(2, 3, figsize=(15, 9.5))
        
        # Subplot 1: Average Waiting Time
        ax = axes[0, 0]
        ax.plot(df_day["Tested Windows"], df_day["avg_wait"], marker='o', color="#e53e3e", linewidth=2)
        ax.set_title("Average Waiting Time (Mins)", fontsize=11, fontweight='bold', color="#0f2042")
        ax.set_xlabel("Number of Windows", fontsize=9)
        ax.set_ylabel("Minutes", fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.5)
        
        # Subplot 2: Queue Length (Max Queue)
        ax = axes[0, 1]
        ax.bar(df_day["Tested Windows"], df_day["max_queue"], color="#3182ce", alpha=0.85, width=0.6)
        ax.set_title("Maximum Queue Length", fontsize=11, fontweight='bold', color="#0f2042")
        ax.set_xlabel("Number of Windows", fontsize=9)
        ax.set_ylabel("Students", fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.5)
        
        # Subplot 3: Throughput (Students Served)
        ax = axes[0, 2]
        ax.bar(df_day["Tested Windows"], df_day["served"], color="#319795", alpha=0.85, width=0.6)
        ax.set_title("Throughput (Students Processed)", fontsize=11, fontweight='bold', color="#0f2042")
        ax.set_xlabel("Number of Windows", fontsize=9)
        ax.set_ylabel("Students", fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.5)
        
        # Subplot 4: Resource Utilization (%)
        ax = axes[1, 0]
        ax.plot(df_day["Tested Windows"], df_day["utilization"], marker='o', color="#dd6b20", linewidth=2)
        ax.set_title("Resource Utilization (%)", fontsize=11, fontweight='bold', color="#0f2042")
        ax.set_xlabel("Number of Windows", fontsize=9)
        ax.set_ylabel("Percentage (%)", fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.5)
        
        # Subplot 5: Processing Time (Avg Service Mins)
        ax = axes[1, 1]
        ax.plot(df_day["Tested Windows"], df_day["avg_service"], marker='o', color="#805ad5", linewidth=2)
        ax.set_title("Processing Time (Avg Service Mins)", fontsize=11, fontweight='bold', color="#0f2042")
        ax.set_xlabel("Number of Windows", fontsize=9)
        ax.set_ylabel("Minutes", fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.5)
        
        # Hide the 6th subplot
        axes[1, 2].axis('off')
        
        # Aesthetic polish
        for r in range(2):
            for c in range(3):
                if r == 1 and c == 2:
                    continue
                ax = axes[r, c]
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#cbd5e0')
                ax.spines['bottom'].set_color('#cbd5e0')
                ax.tick_params(axis='both', which='major', labelsize=8)
                
        plt.tight_layout()
        st.pyplot(fig)

with tab3:
    st.subheader("System Modeling Output Matrices")
    st.info(
        "**⏱ Waiting Time Methodology:** Waiting time is measured from **8:00 AM (office opening)**, "
        "not from when students physically arrived. Students who came early (pre-queue) are counted in "
        "Total Arrivals, but their wait clock starts when the cashier windows open — reflecting what "
        "the office can control, not individual student choices about when to arrive."
    )
    
    selected_win_view = st.selectbox(
        "Filter Data View by Window Count:", sorted(window_analysis.keys()),
        help="Select a specific window layout scenario to inspect its exact numeric results across all 5 simulated operational days."
    )
    df_filtered = df_all[df_all["Tested Windows"] == selected_win_view].copy()
    
    # Formatting outputs for clean business tables
    df_filtered["avg_wait"] = df_filtered["avg_wait"].round(1)
    df_filtered["max_wait"] = df_filtered["max_wait"].round(1)
    df_filtered["utilization"] = df_filtered["utilization"].round(1)
    df_filtered["overtime_hours"] = df_filtered["overtime_hours"].round(2)
    df_filtered["avg_service"] = df_filtered["avg_service"].round(1)
    
    st.dataframe(
        df_filtered.rename(columns={
            "day": "Enrollment Day",
            "incoming": "Total Arrivals (incl. pre-queue)",
            "served": "Students Processed",
            "balked": "Students Balked",
            "avg_wait": "Avg Wait from 8 AM (Mins)",
            "max_wait": "Max Wait from 8 AM (Mins)",
            "utilization": "Cashier Utilization %",
            "overtime_hours": "Overtime Hours Required",
            "max_queue": "Max Queue Length Peak",
            "avg_service": "Avg Processing Time (Mins)"
        }),
        use_container_width=True,
        hide_index=True
    )
<<<<<<< HEAD
# um-enrollment-cashiering-simulation
discrete modeling and simulation
=======
# UM Enrollment Cashiering Simulation Tool

### Discrete Event Simulation of the University of Mindanao (UM) Cashiering System: Determining Optimal Window Capacity for Peak Enrollment Demand

This predictive simulation model analyzes student arrival distributions, queue formations, and transactional throughput at the **University of Mindanao (UM) Cashier's Office**. By simulating operational flows under stochastic constraints, this decision support tool evaluates counter window capacities to mathematically determine optimal staffing levels required to meet peak enrollment demand while minimizing service bottlenecks.

---

##  System Modeling & Simulation (M&S) Architecture

This application is an end-to-end **Discrete Event Simulation (DES)** built using the `SimPy` framework. It evaluates the resource-to-demand mismatch during high-pressure peak enrollment cycles by tracking the mathematical interaction between independent entities and constrained physical resources.

###  Key Operational Features Modeled
* **Saturation of Service Capacity:** Evaluates whether arrival rates during peak intervals consistently exceed the clearing speed of active counter windows.
* **Impact of "Slow-Start" Entities:** Re-enacts how New Students—who require extensive manual data entry and profile registration—occupy windows for longer periods compared to Old Students.
* **Wait Time Escalation:** Quantifies exact student waiting intervals to establish the minimum window count required to maintain service level goals (e.g., an average wait time under 30 minutes).
* **Physical Congestion & Balking:** Simulates line density thresholds where arriving students abandon the queue immediately if the queue length becomes unmanageable.

###  Stochastic Distributions & Assumptions
1. **Interarrival Times:** Generated dynamically via non-homogeneous Exponential Distributions (`random.expovariate`) to accurately mimic multi-interval peak-hour surges.
2. **Service Time Variability:** Transactions for Old Students are governed by a **Normal Distribution**, while New Student service ranges follow a skewed **Lognormal Distribution** to account for complex, inquiry-based delays.
3. **Pre-Queue Dispenser Delays:** Integrates a localized delay (3–5 minutes for New Students; under 1 minute for Old Students) to model queue machine interactions before entering the main line.
4. **Queue Discipline:** Operates on a strict **First-In, First-Out (FIFO)** processing order upon main line entry.

---

##  Tech Stack
* **Language:** Python 3.x
* **Simulation Core:** SimPy (Discrete Event Simulation engine)
* **Web Interface:** Streamlit (Clean, responsive dashboard layout)
* **Data & Analytics:** Pandas, NumPy
* **Visualization:** Matplotlib

---

##  Installation & Local Deployment

Follow these steps to set up and run the simulation platform on your local machine:

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/um-enrollment-cashiering-simulation.git](https://github.com/your-username/um-enrollment-cashiering-simulation.git)
cd um-enrollment-cashiering-simulation
>>>>>>> f94080c (Initial commit)

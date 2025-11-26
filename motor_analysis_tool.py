"""
Advanced 3-Phase Induction Motor Analysis Tool
Features:
- Starting torque calculations (DOL, Star-Delta)
- Dynamic motor simulation with ODE solver
- Real-time visualization
- Professional GUI with auto-scaling
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.integrate import solve_ivp
import math


class InductionMotorModel:
    """Mathematical model for 3-phase squirrel cage induction motor"""

    def __init__(self, rated_power, rated_voltage, rated_speed, poles,
                 starting_current_ratio, full_load_slip):
        """
        Initialize motor parameters

        Args:
            rated_power: Rated power in kW
            rated_voltage: Line voltage in V
            rated_speed: Rated speed in RPM
            poles: Number of poles
            starting_current_ratio: Ist/Ifl ratio
            full_load_slip: Full load slip (per unit)
        """
        self.P_rated = rated_power * 1000  # Convert to Watts
        self.V_rated = rated_voltage
        self.n_rated = rated_speed
        self.poles = poles
        self.Ist_Ifl_ratio = starting_current_ratio
        self.s_fl = full_load_slip

        # Calculate synchronous speed
        self.f = 50  # Frequency in Hz (default)
        self.n_sync = (120 * self.f) / self.poles  # RPM
        self.omega_sync = (2 * np.pi * self.n_sync) / 60  # rad/s

        # Calculate motor parameters
        self._calculate_parameters()

    def _calculate_parameters(self):
        """Calculate equivalent circuit parameters"""
        # Full load torque
        self.omega_fl = (2 * np.pi * self.n_rated) / 60
        self.T_fl = self.P_rated / self.omega_fl

        # Full load current (approximation)
        pf_fl = 0.85  # Assumed power factor at full load
        self.I_fl = self.P_rated / (np.sqrt(3) * self.V_rated * pf_fl * 0.92)  # 92% efficiency

        # Starting current
        self.I_st = self.Ist_Ifl_ratio * self.I_fl

        # Approximate rotor and stator resistance/reactance
        # These are estimated based on typical motor characteristics
        Z_st = self.V_rated / (np.sqrt(3) * self.I_st)
        Z_fl = self.V_rated / (np.sqrt(3) * self.I_fl)

        # Simplified equivalent circuit parameters
        self.R1 = 0.04 * Z_fl  # Stator resistance
        self.X1 = 0.08 * Z_fl  # Stator reactance
        self.Xm = 3.0 * Z_fl   # Magnetizing reactance
        self.R2 = 0.05 * Z_fl  # Rotor resistance
        self.X2 = 0.08 * Z_fl  # Rotor reactance

        # Moment of inertia (estimated)
        self.J = 0.05 * self.P_rated / (self.omega_sync ** 2)  # kg·m²

        # Load torque parameters (quadratic load)
        self.TL_rated = self.T_fl
        self.load_coefficient = self.TL_rated / (self.omega_fl ** 2)

    def calculate_starting_torque_dol(self):
        """
        Calculate starting torque for Direct-On-Line starting

        Returns:
            Starting torque as percentage of full-load torque
        """
        # Using simplified formula: T ∝ I²
        T_st_percentage = (self.Ist_Ifl_ratio ** 2) * 100
        return T_st_percentage

    def calculate_starting_torque_star_delta(self):
        """
        Calculate starting torque for Star-Delta starting

        In star connection:
        - Line voltage across motor = V_line / √3
        - Torque = (1/3) of DOL torque

        Returns:
            Starting torque as percentage of full-load torque
        """
        T_dol = self.calculate_starting_torque_dol()
        T_star = T_dol / 3
        return T_star

    def torque_slip_curve(self, slip):
        """
        Calculate electromagnetic torque using equivalent circuit

        Args:
            slip: Slip value (0 to 1)

        Returns:
            Electromagnetic torque in N·m
        """
        if slip < 0.0001:
            slip = 0.0001  # Avoid division by zero

        # Thevenin equivalent of stator circuit
        Zth = (1j * self.Xm * (self.R1 + 1j * self.X1)) / (self.R1 + 1j * (self.X1 + self.Xm))
        Vth = self.V_rated / np.sqrt(3) * (1j * self.Xm) / (self.R1 + 1j * (self.X1 + self.Xm))
        Vth_mag = abs(Vth)
        Rth = Zth.real
        Xth = Zth.imag

        # Rotor current
        Z_total = np.sqrt((Rth + self.R2/slip)**2 + (Xth + self.X2)**2)
        I2 = Vth_mag / Z_total

        # Electromagnetic torque
        T_em = (3 / self.omega_sync) * I2**2 * (self.R2 / slip)

        return T_em

    def load_torque(self, omega):
        """
        Calculate load torque (quadratic characteristic)

        Args:
            omega: Angular velocity in rad/s

        Returns:
            Load torque in N·m
        """
        if omega < 0:
            omega = 0
        return self.load_coefficient * omega ** 2

    def motor_dynamics(self, t, y, starting_method='DOL'):
        """
        Differential equations for motor dynamics

        Args:
            t: Time
            y: State vector [omega, theta]
            starting_method: 'DOL' or 'Star-Delta'

        Returns:
            Derivative [domega/dt, dtheta/dt]
        """
        omega, theta = y

        # Calculate slip
        if omega < self.omega_sync:
            s = (self.omega_sync - omega) / self.omega_sync
        else:
            s = 0

        # Calculate electromagnetic torque
        if starting_method == 'Star-Delta' and t < 2.0:
            # Star connection for first 2 seconds
            T_em = self.torque_slip_curve(s) / 3
        else:
            # Delta connection (DOL or after star-delta transition)
            T_em = self.torque_slip_curve(s)

        # Calculate load torque
        T_load = self.load_torque(omega)

        # Friction torque (small)
        T_friction = 0.02 * self.T_fl

        # Net torque
        T_net = T_em - T_load - T_friction

        # Angular acceleration
        domega_dt = T_net / self.J
        dtheta_dt = omega

        return [domega_dt, dtheta_dt]

    def current_vs_slip(self, slip, starting_method='DOL'):
        """Calculate motor current for given slip"""
        if slip < 0.0001:
            slip = 0.0001

        # Thevenin equivalent
        Zth = (1j * self.Xm * (self.R1 + 1j * self.X1)) / (self.R1 + 1j * (self.X1 + self.Xm))
        Vth = self.V_rated / np.sqrt(3) * (1j * self.Xm) / (self.R1 + 1j * (self.X1 + self.Xm))
        Vth_mag = abs(Vth)
        Rth = Zth.real
        Xth = Zth.imag

        # Total impedance
        Z_total = np.sqrt((Rth + self.R2/slip)**2 + (Xth + self.X2)**2)
        I_phase = Vth_mag / Z_total
        I_line = I_phase  # For delta or equivalent

        if starting_method == 'Star-Delta':
            I_line = I_line / np.sqrt(3)  # Star connection reduces line current

        return I_line


class MotorAnalysisTool:
    """Main GUI application for motor analysis"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced 3-Phase Induction Motor Analysis Tool")
        self.root.geometry("1400x900")

        # Simulation state
        self.simulation_running = False
        self.simulation_data = None
        self.motor = None

        # Configure grid weight for auto-scaling
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create main container
        self.main_container = ttk.Frame(root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure main container grid
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)

        # Create UI components
        self.create_menu()
        self.create_input_panel()
        self.create_control_panel()
        self.create_visualization_panel()
        self.create_results_panel()

        # Bind window resize event
        self.root.bind('<Configure>', self.on_window_resize)

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Results", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_input_panel(self):
        """Create input parameters panel"""
        input_frame = ttk.LabelFrame(self.main_container, text="Motor Parameters",
                                      padding="10")
        input_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N))

        # Motor parameters
        params = [
            ("Rated Power (kW):", "power", "15"),
            ("Rated Voltage (V):", "voltage", "415"),
            ("Rated Speed (RPM):", "speed", "1440"),
            ("Number of Poles:", "poles", "4"),
            ("Starting Current Ratio (Ist/Ifl):", "current_ratio", "6"),
            ("Full Load Slip (%):", "slip", "4"),
        ]

        self.input_vars = {}

        for i, (label, key, default) in enumerate(params):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(input_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
            self.input_vars[key] = var

        # Starting method selection
        ttk.Label(input_frame, text="Starting Method:").grid(row=len(params), column=0,
                                                              sticky=tk.W, pady=3)
        self.starting_method_var = tk.StringVar(value="DOL")
        method_combo = ttk.Combobox(input_frame, textvariable=self.starting_method_var,
                                     values=["DOL", "Star-Delta"], state="readonly", width=13)
        method_combo.grid(row=len(params), column=1, sticky=(tk.W, tk.E), pady=3, padx=5)

        # Calculate button
        calc_btn = ttk.Button(input_frame, text="Calculate Starting Torque",
                              command=self.calculate_starting_torque)
        calc_btn.grid(row=len(params)+1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        # Configure column weights
        input_frame.grid_columnconfigure(1, weight=1)

    def create_control_panel(self):
        """Create control panel with sliders"""
        control_frame = ttk.LabelFrame(self.main_container, text="Simulation Controls",
                                        padding="10")
        control_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Simulation time slider
        ttk.Label(control_frame, text="Simulation Time (s):").grid(row=0, column=0,
                                                                     sticky=tk.W, pady=5)
        self.sim_time_var = tk.DoubleVar(value=5.0)
        sim_time_slider = ttk.Scale(control_frame, from_=1.0, to=10.0,
                                      variable=self.sim_time_var, orient=tk.HORIZONTAL)
        sim_time_slider.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.sim_time_label = ttk.Label(control_frame, text="5.0 s")
        self.sim_time_label.grid(row=0, column=2, sticky=tk.W, pady=5)
        sim_time_slider.config(command=lambda v: self.sim_time_label.config(text=f"{float(v):.1f} s"))

        # Load torque slider
        ttk.Label(control_frame, text="Load Torque (% of rated):").grid(row=1, column=0,
                                                                          sticky=tk.W, pady=5)
        self.load_torque_var = tk.DoubleVar(value=100.0)
        load_slider = ttk.Scale(control_frame, from_=0, to=150,
                                 variable=self.load_torque_var, orient=tk.HORIZONTAL)
        load_slider.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.load_label = ttk.Label(control_frame, text="100 %")
        self.load_label.grid(row=1, column=2, sticky=tk.W, pady=5)
        load_slider.config(command=lambda v: self.load_label.config(text=f"{float(v):.0f} %"))

        # ODE Solver selection
        ttk.Label(control_frame, text="ODE Solver:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.solver_var = tk.StringVar(value="RK45")
        solver_combo = ttk.Combobox(control_frame, textvariable=self.solver_var,
                                     values=["RK45", "RK23", "Radau", "BDF", "Euler"],
                                     state="readonly", width=10)
        solver_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky=(tk.W, tk.E))

        self.start_btn = ttk.Button(button_frame, text="Start Simulation",
                                     command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.stop_btn = ttk.Button(button_frame, text="Stop",
                                    command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.reset_btn = ttk.Button(button_frame, text="Reset",
                                     command=self.reset_simulation)
        self.reset_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Configure column weights
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_rowconfigure(4, weight=1)

    def create_visualization_panel(self):
        """Create visualization panel with plots"""
        viz_frame = ttk.LabelFrame(self.main_container, text="Real-Time Visualization",
                                    padding="10")
        viz_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5,
                       sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 8), dpi=100)

        # Create subplots
        self.ax1 = self.fig.add_subplot(3, 1, 1)
        self.ax2 = self.fig.add_subplot(3, 1, 2)
        self.ax3 = self.fig.add_subplot(3, 1, 3)

        self.fig.tight_layout(pad=3.0)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize plots
        self.init_plots()

    def create_results_panel(self):
        """Create results display panel"""
        results_frame = ttk.LabelFrame(self.main_container, text="Calculation Results",
                                        padding="10")
        results_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5,
                           sticky=(tk.W, tk.E))

        # Results text widget
        self.results_text = tk.Text(results_frame, height=8, width=80,
                                     font=("Courier", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL,
                                   command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)

    def init_plots(self):
        """Initialize empty plots"""
        # Speed plot
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Speed (RPM)')
        self.ax1.set_title('Motor Speed vs Time')
        self.ax1.grid(True, alpha=0.3)

        # Torque plot
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Torque (N·m)')
        self.ax2.set_title('Electromagnetic Torque vs Time')
        self.ax2.grid(True, alpha=0.3)

        # Current plot
        self.ax3.set_xlabel('Time (s)')
        self.ax3.set_ylabel('Current (A)')
        self.ax3.set_title('Stator Current vs Time')
        self.ax3.grid(True, alpha=0.3)

        self.canvas.draw()

    def calculate_starting_torque(self):
        """Calculate and display starting torque"""
        try:
            # Get input values
            power = float(self.input_vars['power'].get())
            voltage = float(self.input_vars['voltage'].get())
            speed = float(self.input_vars['speed'].get())
            poles = int(self.input_vars['poles'].get())
            current_ratio = float(self.input_vars['current_ratio'].get())
            slip = float(self.input_vars['slip'].get()) / 100  # Convert to per unit

            # Create motor model
            self.motor = InductionMotorModel(power, voltage, speed, poles,
                                             current_ratio, slip)

            # Calculate starting torques
            T_st_dol = self.motor.calculate_starting_torque_dol()
            T_st_star_delta = self.motor.calculate_starting_torque_star_delta()

            # Display results
            results = f"""
{'='*80}
STARTING TORQUE CALCULATION RESULTS
{'='*80}

Motor Specifications:
  Rated Power:              {power} kW
  Rated Voltage:            {voltage} V
  Rated Speed:              {speed} RPM
  Number of Poles:          {poles}
  Synchronous Speed:        {self.motor.n_sync:.0f} RPM
  Full Load Slip:           {slip*100:.2f} %
  Starting Current Ratio:   {current_ratio}

Calculated Parameters:
  Full Load Torque:         {self.motor.T_fl:.2f} N·m
  Full Load Current:        {self.motor.I_fl:.2f} A
  Starting Current (DOL):   {self.motor.I_st:.2f} A

Starting Torque Results:
  (a) Direct-On-Line (DOL):     {T_st_dol:.2f} % of full-load torque
  (b) Star-Delta Starter:       {T_st_star_delta:.2f} % of full-load torque

Equivalent Circuit Parameters:
  Stator Resistance (R1):   {self.motor.R1:.4f} Ω
  Stator Reactance (X1):    {self.motor.X1:.4f} Ω
  Rotor Resistance (R2):    {self.motor.R2:.4f} Ω
  Rotor Reactance (X2):     {self.motor.X2:.4f} Ω
  Magnetizing Reactance:    {self.motor.Xm:.4f} Ω
  Moment of Inertia:        {self.motor.J:.4f} kg·m²

{'='*80}
THEORETICAL EXPLANATION:

For Direct-On-Line (DOL) Starting:
  - Full rated voltage is applied to motor terminals
  - Starting torque T_st ∝ (I_st)²
  - T_st/T_fl = (I_st/I_fl)² = {current_ratio}² = {T_st_dol:.0f}%

For Star-Delta Starting:
  - Motor starts in star connection, then switches to delta
  - In star: Phase voltage = Line voltage / √3
  - Torque ∝ V², so T_star = T_delta / 3
  - T_st_star = {T_st_dol:.0f}% / 3 = {T_st_star_delta:.0f}%

{'='*80}
"""

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, results)

            messagebox.showinfo("Success", "Starting torque calculated successfully!")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid numeric values.\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An error occurred:\n{str(e)}")

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.motor is None:
            messagebox.showwarning("Warning", "Please calculate starting torque first!")
            return

        try:
            self.simulation_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

            # Update load torque coefficient based on slider
            load_percentage = self.load_torque_var.get() / 100.0
            self.motor.load_coefficient = self.motor.TL_rated * load_percentage / (self.motor.omega_fl ** 2)

            # Simulation parameters
            t_span = (0, self.sim_time_var.get())
            y0 = [0, 0]  # Initial conditions: [omega=0, theta=0]

            # Get starting method
            starting_method = self.starting_method_var.get()

            # Select ODE solver
            solver = self.solver_var.get()

            if solver == 'Euler':
                # Custom Euler method implementation
                self.simulation_data = self.euler_solver(t_span, y0, starting_method)
            else:
                # Use scipy's solve_ivp
                sol = solve_ivp(
                    lambda t, y: self.motor.motor_dynamics(t, y, starting_method),
                    t_span, y0, method=solver, dense_output=True,
                    max_step=0.01
                )

                # Generate time points
                t_eval = np.linspace(t_span[0], t_span[1], 500)
                y_eval = sol.sol(t_eval)

                # Extract results
                omega = y_eval[0, :]
                speed = omega * 60 / (2 * np.pi)  # Convert to RPM

                # Calculate torque and current at each time point
                torque = []
                current = []

                for i, t in enumerate(t_eval):
                    s = (self.motor.omega_sync - omega[i]) / self.motor.omega_sync
                    if s < 0:
                        s = 0

                    if starting_method == 'Star-Delta' and t < 2.0:
                        T = self.motor.torque_slip_curve(s) / 3
                        I = self.motor.current_vs_slip(s, 'Star-Delta')
                    else:
                        T = self.motor.torque_slip_curve(s)
                        I = self.motor.current_vs_slip(s, 'DOL')

                    torque.append(T)
                    current.append(I)

                self.simulation_data = {
                    't': t_eval,
                    'speed': speed,
                    'torque': np.array(torque),
                    'current': np.array(current)
                }

            # Plot results
            self.plot_simulation_results()

            self.simulation_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

            messagebox.showinfo("Success", "Simulation completed successfully!")

        except Exception as e:
            self.simulation_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            messagebox.showerror("Simulation Error", f"An error occurred:\n{str(e)}")

    def euler_solver(self, t_span, y0, starting_method):
        """Custom Euler method for ODE solving"""
        dt = 0.01  # Time step
        t = np.arange(t_span[0], t_span[1], dt)
        n_steps = len(t)

        # Initialize arrays
        omega = np.zeros(n_steps)
        theta = np.zeros(n_steps)
        omega[0], theta[0] = y0

        # Euler integration
        for i in range(1, n_steps):
            dydt = self.motor.motor_dynamics(t[i-1], [omega[i-1], theta[i-1]], starting_method)
            omega[i] = omega[i-1] + dydt[0] * dt
            theta[i] = theta[i-1] + dydt[1] * dt

        # Convert to RPM
        speed = omega * 60 / (2 * np.pi)

        # Calculate torque and current
        torque = []
        current = []

        for i in range(n_steps):
            s = (self.motor.omega_sync - omega[i]) / self.motor.omega_sync
            if s < 0:
                s = 0

            if starting_method == 'Star-Delta' and t[i] < 2.0:
                T = self.motor.torque_slip_curve(s) / 3
                I = self.motor.current_vs_slip(s, 'Star-Delta')
            else:
                T = self.motor.torque_slip_curve(s)
                I = self.motor.current_vs_slip(s, 'DOL')

            torque.append(T)
            current.append(I)

        return {
            't': t,
            'speed': speed,
            'torque': np.array(torque),
            'current': np.array(current)
        }

    def plot_simulation_results(self):
        """Plot simulation results"""
        if self.simulation_data is None:
            return

        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Plot speed
        self.ax1.plot(self.simulation_data['t'], self.simulation_data['speed'],
                      'b-', linewidth=2, label='Motor Speed')
        self.ax1.axhline(y=self.motor.n_rated, color='r', linestyle='--',
                         label=f'Rated Speed ({self.motor.n_rated:.0f} RPM)')
        self.ax1.set_xlabel('Time (s)', fontsize=10)
        self.ax1.set_ylabel('Speed (RPM)', fontsize=10)
        self.ax1.set_title('Motor Speed vs Time', fontsize=11, fontweight='bold')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(loc='best', fontsize=9)

        # Plot torque
        self.ax2.plot(self.simulation_data['t'], self.simulation_data['torque'],
                      'g-', linewidth=2, label='Electromagnetic Torque')
        self.ax2.axhline(y=self.motor.T_fl, color='r', linestyle='--',
                         label=f'Full Load Torque ({self.motor.T_fl:.1f} N·m)')
        self.ax2.set_xlabel('Time (s)', fontsize=10)
        self.ax2.set_ylabel('Torque (N·m)', fontsize=10)
        self.ax2.set_title('Electromagnetic Torque vs Time', fontsize=11, fontweight='bold')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend(loc='best', fontsize=9)

        # Plot current
        self.ax3.plot(self.simulation_data['t'], self.simulation_data['current'],
                      'r-', linewidth=2, label='Stator Current')
        self.ax3.axhline(y=self.motor.I_fl, color='g', linestyle='--',
                         label=f'Full Load Current ({self.motor.I_fl:.1f} A)')
        self.ax3.set_xlabel('Time (s)', fontsize=10)
        self.ax3.set_ylabel('Current (A)', fontsize=10)
        self.ax3.set_title('Stator Current vs Time', fontsize=11, fontweight='bold')
        self.ax3.grid(True, alpha=0.3)
        self.ax3.legend(loc='best', fontsize=9)

        # Mark star-delta transition if applicable
        if self.starting_method_var.get() == 'Star-Delta':
            for ax in [self.ax1, self.ax2, self.ax3]:
                ax.axvline(x=2.0, color='orange', linestyle=':', linewidth=2,
                           label='Star→Delta Transition')
                ax.legend(loc='best', fontsize=9)

        self.fig.tight_layout()
        self.canvas.draw()

    def stop_simulation(self):
        """Stop running simulation"""
        self.simulation_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def reset_simulation(self):
        """Reset simulation and clear plots"""
        self.simulation_data = None
        self.init_plots()
        self.results_text.delete(1.0, tk.END)

    def save_results(self):
        """Save simulation results to file"""
        if self.simulation_data is None:
            messagebox.showwarning("Warning", "No simulation data to save!")
            return

        try:
            filename = f"motor_simulation_results.txt"
            with open(filename, 'w') as f:
                f.write("Motor Simulation Results\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Starting Method: {self.starting_method_var.get()}\n")
                f.write(f"Simulation Time: {self.sim_time_var.get()} s\n")
                f.write(f"ODE Solver: {self.solver_var.get()}\n\n")
                f.write("Time(s)\tSpeed(RPM)\tTorque(Nm)\tCurrent(A)\n")

                for i in range(len(self.simulation_data['t'])):
                    f.write(f"{self.simulation_data['t'][i]:.3f}\t"
                           f"{self.simulation_data['speed'][i]:.2f}\t"
                           f"{self.simulation_data['torque'][i]:.2f}\t"
                           f"{self.simulation_data['current'][i]:.2f}\n")

            messagebox.showinfo("Success", f"Results saved to {filename}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save results:\n{str(e)}")

    def show_about(self):
        """Show about dialog"""
        about_text = """
Advanced 3-Phase Induction Motor Analysis Tool

Version: 1.0
Developer: Electrical Engineering Lab

Features:
• Starting torque calculations (DOL & Star-Delta)
• Dynamic motor simulation with multiple ODE solvers
• Real-time visualization of speed, torque, and current
• Professional GUI with auto-scaling
• Comprehensive motor modeling

This tool is designed for educational and practical use
in electrical engineering applications.
        """
        messagebox.showinfo("About", about_text)

    def on_window_resize(self, event):
        """Handle window resize event for auto-scaling"""
        # Only resize canvas if it's a window resize event
        if event.widget == self.root:
            # Update canvas size
            try:
                self.fig.tight_layout()
                self.canvas.draw()
            except:
                pass  # Ignore errors during resize


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = MotorAnalysisTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()

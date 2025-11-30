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


class ShuntMotorCase:
    """Utility class to evaluate DC shunt motor scenarios."""

    def __init__(self, voltage=230.0, line_current=40.0, speed_rpm=1100.0,
                 output_power_hp=10.8, core_loss=200.0, friction_loss=180.0,
                 brush_loss=37.0, stray_loss=37.0, armature_resistance=0.25,
                 field_resistance=230.0):
        self.voltage = voltage
        self.line_current = line_current
        self.speed_rpm = speed_rpm
        self.output_power_hp = output_power_hp
        self.core_loss = core_loss
        self.friction_loss = friction_loss
        self.brush_loss = brush_loss
        self.stray_loss = stray_loss
        self.armature_resistance = armature_resistance
        self.field_resistance = field_resistance

    @property
    def field_current(self):
        return self.voltage / self.field_resistance

    def _armature_current(self, line_current=None):
        if line_current is None:
            line_current = self.line_current
        return line_current - self.field_current

    def _armature_copper_loss(self, armature_current):
        return (armature_current ** 2) * self.armature_resistance

    def _constant_losses(self):
        return self.field_current ** 2 * self.field_resistance + self.core_loss + self.friction_loss + self.brush_loss + self.stray_loss

    def evaluate(self, output_power_watts=None):
        """Return efficiency and electrical operating point.

        Args:
            output_power_watts: Optional mechanical output power. If omitted, use rated case.
        """
        if output_power_watts is None:
            output_power_watts = self.output_power_hp * 746

        constant_losses = self._constant_losses()

        # Solve for armature current that satisfies power balance when output is specified
        # Input power: V * (Ia + If)
        # Output power: specified
        # Losses: constant_losses + Ia^2 * Ra
        # => V * (Ia + If) = output + constant_losses + Ia^2 * Ra
        a = self.armature_resistance
        b = -self.voltage
        c = (output_power_watts + constant_losses) - self.voltage * self.field_current

        discriminant = b ** 2 - 4 * a * c
        if discriminant < 0:
            raise ValueError("Invalid operating point: negative discriminant")

        ia_candidate_1 = (-b + math.sqrt(discriminant)) / (2 * a)
        ia_candidate_2 = (-b - math.sqrt(discriminant)) / (2 * a)
        ia = ia_candidate_1 if ia_candidate_1 > 0 else ia_candidate_2

        pin = self.voltage * (ia + self.field_current)
        total_losses = constant_losses + self._armature_copper_loss(ia)
        efficiency = output_power_watts / pin
        back_emf = self.voltage - ia * self.armature_resistance

        # Base back emf for speed scaling (rated case)
        ia_rated = self._armature_current()
        e_rated = self.voltage - ia_rated * self.armature_resistance
        speed_rpm = self.speed_rpm * back_emf / e_rated

        return {
            "armature_current": ia,
            "input_power": pin,
            "losses": total_losses,
            "efficiency": efficiency,
            "speed_rpm": speed_rpm,
            "back_emf": back_emf
        }


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
        self.shunt_case = ShuntMotorCase()

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
        self.create_shunt_motor_panel()

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

        # Advanced control options
        advanced_frame = ttk.LabelFrame(control_frame, text="Advanced Controls",
                                        padding="8")
        advanced_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(advanced_frame, text="Control Strategy:").grid(row=0, column=0, sticky=tk.W)
        self.control_strategy = tk.StringVar(value="Vector")
        strategy_combo = ttk.Combobox(advanced_frame, textvariable=self.control_strategy,
                                      values=["V/f", "Vector", "DTC", "FOC"], width=12,
                                      state="readonly")
        strategy_combo.grid(row=0, column=1, padx=4, pady=2, sticky=(tk.W, tk.E))

        ttk.Label(advanced_frame, text="Field Weakening (%):").grid(row=1, column=0, sticky=tk.W)
        self.field_weakening = tk.DoubleVar(value=0.0)
        ttk.Scale(advanced_frame, from_=0, to=30, variable=self.field_weakening,
                  orient=tk.HORIZONTAL).grid(row=1, column=1, padx=4, pady=2, sticky=(tk.W, tk.E))

        ttk.Label(advanced_frame, text="Thermal Limit (°C):").grid(row=2, column=0, sticky=tk.W)
        self.thermal_limit = tk.DoubleVar(value=110.0)
        ttk.Scale(advanced_frame, from_=60, to=150, variable=self.thermal_limit,
                  orient=tk.HORIZONTAL).grid(row=2, column=1, padx=4, pady=2, sticky=(tk.W, tk.E))

        ttk.Label(advanced_frame, text="Derating (%):").grid(row=3, column=0, sticky=tk.W)
        self.derating = tk.DoubleVar(value=0.0)
        ttk.Scale(advanced_frame, from_=0, to=40, variable=self.derating,
                  orient=tk.HORIZONTAL).grid(row=3, column=1, padx=4, pady=2, sticky=(tk.W, tk.E))

        self.power_consumption_var = tk.StringVar(value="Power Consumption: N/A")
        ttk.Label(advanced_frame, textvariable=self.power_consumption_var,
                  foreground="blue").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)

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

        # Create subplots (2x2 grid for multi-physics visualization)
        self.ax1 = self.fig.add_subplot(2, 2, 1)
        self.ax2 = self.fig.add_subplot(2, 2, 2)
        self.ax3 = self.fig.add_subplot(2, 2, 3)
        self.ax4 = self.fig.add_subplot(2, 2, 4)

        self.fig.tight_layout(pad=3.0)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize plots
        self.init_plots()

    def create_results_panel(self):
        """Create results display panel with tabs"""
        results_frame = ttk.LabelFrame(self.main_container, text="Calculation Results",
                                        padding="10")
        results_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5,
                           sticky=(tk.W, tk.E, tk.N, tk.S))

        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        # Electrical results tab
        electrical_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(electrical_tab, text="Electrical")
        self.results_text = tk.Text(electrical_tab, height=8, width=80, font=("Courier", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Economic analysis tab
        economic_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(economic_tab, text="Economic / Losses")
        self.economic_text = tk.Text(economic_tab, height=8, width=80, font=("Courier", 10))
        self.economic_text.pack(fill=tk.BOTH, expand=True)

        # Multi-physics tab
        multiphysics_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(multiphysics_tab, text="Multi-Physics")
        self.multiphysics_text = tk.Text(multiphysics_tab, height=8, width=80, font=("Courier", 10))
        self.multiphysics_text.pack(fill=tk.BOTH, expand=True)

    def create_shunt_motor_panel(self):
        """Panel dedicated to DC shunt motor case study and economic analysis."""
        panel = ttk.LabelFrame(self.main_container, text="DC Shunt Motor Study & Economics", padding="10")
        panel.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(panel, text="Output Reduction (%):").grid(row=0, column=0, sticky=tk.W)
        self.output_reduction = tk.DoubleVar(value=50.0)
        ttk.Scale(panel, from_=0, to=80, variable=self.output_reduction, orient=tk.HORIZONTAL,
                  command=lambda v: self.output_reduction_label.config(text=f"{float(v):.0f} %")).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=4)
        self.output_reduction_label = ttk.Label(panel, text="50 %")
        self.output_reduction_label.grid(row=0, column=2, sticky=tk.W)

        self.run_shunt_btn = ttk.Button(panel, text="Solve Shunt Motor Case", command=self.solve_shunt_case)
        self.run_shunt_btn.grid(row=0, column=3, padx=6)

        # Economic inputs
        ttk.Label(panel, text="Energy Cost ($/kWh):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.energy_cost = tk.DoubleVar(value=0.12)
        ttk.Entry(panel, textvariable=self.energy_cost, width=10).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(panel, text="Operating Hours/yr:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.operating_hours = tk.DoubleVar(value=3000)
        ttk.Entry(panel, textvariable=self.operating_hours, width=10).grid(row=1, column=3, sticky=tk.W)

        ttk.Label(panel, text="Maintenance ($/yr):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.maintenance_cost = tk.DoubleVar(value=450)
        ttk.Entry(panel, textvariable=self.maintenance_cost, width=10).grid(row=2, column=1, sticky=tk.W)

        ttk.Button(panel, text="Update Economic Analysis", command=self.update_economic_analysis).grid(
            row=2, column=3, padx=6, pady=2)

        panel.grid_columnconfigure(1, weight=1)
        panel.grid_columnconfigure(3, weight=1)

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

        # Thermal and stress plot
        self.ax4.set_xlabel('Time (s)')
        self.ax4.set_ylabel('Temp (°C) / Stress (MPa)')
        self.ax4.set_title('Thermal & Mechanical Response')
        self.ax4.grid(True, alpha=0.3)

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

    def solve_shunt_case(self):
        """Solve the DC shunt motor example and update reports."""
        try:
            base_case = self.shunt_case.evaluate()
            reduced_power = self.shunt_case.output_power_hp * 746 * (1 - self.output_reduction.get() / 100)
            reduced_case = self.shunt_case.evaluate(output_power_watts=reduced_power)

            summary = f"""
{'='*80}
DC SHUNT MOTOR PERFORMANCE
{'='*80}
Rated Output Power:      {self.shunt_case.output_power_hp:.2f} hp
Line Voltage:            {self.shunt_case.voltage:.1f} V
Line Current:            {self.shunt_case.line_current:.1f} A
Rated Speed:             {self.shunt_case.speed_rpm:.1f} rpm

(a) Rated Condition:
  Input Power:           {base_case['input_power']:.2f} W
  Total Losses:          {base_case['losses']:.2f} W
  Efficiency:            {base_case['efficiency']*100:.2f} %
  Back EMF:              {base_case['back_emf']:.2f} V

(b) Reduced Output ({self.output_reduction.get():.0f}% decrease):
  Output Power:          {reduced_power:.2f} W
  Input Power:           {reduced_case['input_power']:.2f} W
  Efficiency:            {reduced_case['efficiency']*100:.2f} %
  Estimated Speed:       {reduced_case['speed_rpm']:.1f} rpm
  Armature Current:      {reduced_case['armature_current']:.2f} A
{'='*80}
"""

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, summary)
            self.results_notebook.select(0)

            self.multiphysics_text.delete(1.0, tk.END)
            self.multiphysics_text.insert(1.0, "Loss Breakdown (Rated):\n")
            self.multiphysics_text.insert(tk.END, f"  Constant Losses: {self.shunt_case._constant_losses():.2f} W\n")
            self.multiphysics_text.insert(tk.END, f"  Armature Copper Loss: {self.shunt_case._armature_copper_loss(base_case['armature_current']):.2f} W\n")
            self.multiphysics_text.insert(tk.END, f"  Iron/Core Loss: {self.shunt_case.core_loss:.2f} W\n")
            self.multiphysics_text.insert(tk.END, f"  Friction & Windage: {self.shunt_case.friction_loss:.2f} W\n")
            self.multiphysics_text.insert(tk.END, f"  Stray Load Loss: {self.shunt_case.stray_loss:.2f} W\n")

            self.update_economic_analysis()

            messagebox.showinfo("Shunt Motor", "DC shunt motor calculations completed")
        except Exception as exc:
            messagebox.showerror("Error", f"Unable to solve shunt motor case:\n{exc}")

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

            # Multi-physics calculations
            multiphysics = self.compute_multiphysics_data(
                self.simulation_data['t'],
                self.simulation_data['torque'],
                self.simulation_data['current']
            )

            self.simulation_data.update(multiphysics)

            # Update power consumption indicator
            avg_power = np.mean(self.simulation_data['current']) * self.motor.V_rated * np.sqrt(3)
            derate_factor = 1 - self.derating.get() / 100
            self.power_consumption_var.set(
                f"Power Consumption: {avg_power * derate_factor/1000:.2f} kW (derated)"
            )

            # Plot results
            self.plot_simulation_results()
            self.refresh_multiphysics_text()
            self.update_economic_analysis()

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

    def compute_multiphysics_data(self, t, torque, current):
        """Estimate coupled electromagnetic-thermal-mechanical behavior."""
        # Simple thermal RC model
        ambient = 25.0
        tau = 8.0  # thermal time constant
        k_loss = 0.12  # temperature rise per watt-s
        temperatures = [ambient]

        # Loss breakdowns (approximate)
        copper_loss = (current ** 2) * (self.motor.R1 + self.motor.R2)
        iron_loss = 0.015 * self.motor.P_rated * np.ones_like(current)
        mech_loss = 0.02 * np.abs(torque)

        dt = np.diff(t, prepend=t[0])
        for i in range(1, len(t)):
            loss_total = copper_loss[i] + iron_loss[i] + mech_loss[i]
            dTdt = k_loss * loss_total - (temperatures[-1] - ambient) / tau
            temperatures.append(temperatures[-1] + dTdt * dt[i])

        temperatures = np.array(temperatures)

        # Mechanical stress estimation (arbitrary scaling for visualization)
        stress = 0.01 * np.abs(torque)  # MPa equivalent

        # Loss detail for reporting
        loss_breakdown = {
            'copper': float(np.mean(copper_loss)),
            'iron': float(np.mean(iron_loss)),
            'mechanical': float(np.mean(mech_loss))
        }

        return {
            'temperature': temperatures,
            'stress': stress,
            'loss_breakdown': loss_breakdown
        }

    def refresh_multiphysics_text(self):
        """Update multi-physics tab with latest simulation insights."""
        if self.simulation_data is None:
            return

        self.multiphysics_text.delete(1.0, tk.END)
        temp = self.simulation_data.get('temperature', [])
        stress = self.simulation_data.get('stress', [])
        losses = self.simulation_data.get('loss_breakdown', {})

        if len(temp) > 0:
            self.multiphysics_text.insert(tk.END, f"Peak Temperature: {np.max(temp):.2f} °C\n")
            self.multiphysics_text.insert(tk.END, f"Average Temperature: {np.mean(temp):.2f} °C\n")

        if len(stress) > 0:
            self.multiphysics_text.insert(tk.END, f"Peak Shaft Stress (eq): {np.max(stress):.2f} MPa\n")

        if losses:
            self.multiphysics_text.insert(tk.END, "Loss Breakdown (avg):\n")
            for k, v in losses.items():
                self.multiphysics_text.insert(tk.END, f"  {k.capitalize():<12}: {v:.2f} W\n")

        self.multiphysics_text.insert(tk.END, "\nCoupled electromagnetic-thermal model tracks temperature rise\n"
                                          "while mechanical stress estimation monitors shaft loading."
                                          " Use derating slider to keep temperatures below limits.")

    def update_economic_analysis(self):
        """Update economic analysis tab based on latest data."""
        try:
            if self.simulation_data is not None and 'current' in self.simulation_data:
                avg_current = np.mean(self.simulation_data['current'])
                avg_power_kw = avg_current * self.motor.V_rated * np.sqrt(3) / 1000
            else:
                avg_power_kw = self.shunt_case.voltage * self.shunt_case.line_current / 1000

            annual_energy = avg_power_kw * self.operating_hours.get()
            energy_cost = annual_energy * self.energy_cost.get()
            total_cost = energy_cost + self.maintenance_cost.get()

            self.economic_text.delete(1.0, tk.END)
            self.economic_text.insert(1.0, f"Average Demand: {avg_power_kw:.2f} kW\n")
            self.economic_text.insert(tk.END, f"Annual Energy: {annual_energy:.1f} kWh\n")
            self.economic_text.insert(tk.END, f"Energy Cost: ${energy_cost:,.2f}\n")
            self.economic_text.insert(tk.END, f"Maintenance: ${self.maintenance_cost.get():,.2f}\n")
            self.economic_text.insert(tk.END, f"Total Annual Cost: ${total_cost:,.2f}\n")

            if self.simulation_data is not None and 'loss_breakdown' in self.simulation_data:
                losses = self.simulation_data['loss_breakdown']
                self.economic_text.insert(tk.END, "\nLoss Breakdown for Efficiency Tuning:\n")
                for k, v in losses.items():
                    self.economic_text.insert(tk.END, f"  {k.capitalize():<12}: {v:.2f} W\n")
        except Exception as exc:
            messagebox.showwarning("Economic Analysis", f"Unable to update economics: {exc}")

    def plot_simulation_results(self):
        """Plot simulation results"""
        if self.simulation_data is None:
            return

        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()

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

        # Plot thermal and mechanical response
        self.ax4.plot(self.simulation_data['t'], self.simulation_data.get('temperature', []),
                      color='orange', linewidth=2, label='Winding Temp')
        self.ax4.plot(self.simulation_data['t'], self.simulation_data.get('stress', []),
                      color='purple', linewidth=2, linestyle='--', label='Shaft Stress (MPa eq)')
        self.ax4.axhline(y=self.thermal_limit.get(), color='red', linestyle=':',
                         label='Thermal Limit')
        self.ax4.set_xlabel('Time (s)', fontsize=10)
        self.ax4.set_ylabel('Temp / Stress', fontsize=10)
        self.ax4.set_title('Coupled Thermal & Mechanical Response', fontsize=11, fontweight='bold')
        self.ax4.grid(True, alpha=0.3)
        self.ax4.legend(loc='best', fontsize=9)

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
• Professional GUI with auto-scaling and tabbed results
• Comprehensive motor modeling, economics, and multi-physics views
• DC shunt motor efficiency calculator for quick case studies

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

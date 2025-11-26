# Advanced 3-Phase Induction Motor Analysis Tool

## Overview
A professional Python-based tool for analyzing 3-phase squirrel cage induction motors with comprehensive GUI, dynamic simulation, and real-time visualization.

## Features

### 1. Starting Torque Calculations
- **Direct-On-Line (DOL) Starting**: Full voltage applied at starting
- **Star-Delta Starting**: Reduced voltage starting method
- Theoretical calculations based on motor equivalent circuit

### 2. Dynamic Motor Simulation
- Real-time ODE solving with multiple solvers:
  - **RK45**: 4th/5th order Runge-Kutta (default, high accuracy)
  - **RK23**: 2nd/3rd order Runge-Kutta (faster)
  - **Radau**: Implicit method (stiff problems)
  - **BDF**: Backward Differentiation Formula (stiff problems)
  - **Euler**: Forward Euler method (educational)

### 3. Professional GUI
- Input parameter panel with validation
- Control sliders for interactive adjustment
- Real-time visualization with matplotlib
- Auto-scaling on window resize
- Professional menu system

### 4. Comprehensive Visualization
- Motor speed vs time
- Electromagnetic torque vs time
- Stator current vs time
- Clear indication of star-delta transition

## Theoretical Background

### Problem Statement
A 3-phase squirrel cage induction motor takes a starting current of 6 times the full-load current.
Find the starting torque as a percentage of full-load torque if the motor is started:
- (a) Direct-on-line (DOL)
- (b) Through a star-delta starter
- Full-load slip = 4%

### Solution

#### (a) Direct-On-Line (DOL) Starting

For a squirrel cage induction motor, torque is proportional to the square of the current:

```
T ∝ I²
```

Therefore:
```
T_st / T_fl = (I_st / I_fl)²
T_st / T_fl = (6)² = 36
T_st = 3600% of full-load torque
```

**Answer: 3600% or 36 times the full-load torque**

#### (b) Star-Delta Starting

In star-delta starting:
- Motor starts in star (Y) connection
- Then switches to delta (Δ) connection after reaching ~80% speed

In star connection:
- Phase voltage = Line voltage / √3
- Torque ∝ V²
- Therefore: T_star = T_delta / 3

```
T_st_star = T_st_DOL / 3
T_st_star = 3600% / 3 = 1200%
T_st_star = 12 times the full-load torque
```

**Answer: 1200% or 12 times the full-load torque**

### Motor Equivalent Circuit

The tool uses the IEEE recommended equivalent circuit:

```
        R1      X1        X2      R2/s
    o---WWW----XXXX----+----XXXX---WWW---o
         |              |                 |
         |             XXX Xm             |
         |             XXX                |
         |              |                 |
    o-------------------+-----------------o

Where:
- R1: Stator resistance
- X1: Stator leakage reactance
- R2: Rotor resistance (referred to stator)
- X2: Rotor leakage reactance (referred to stator)
- Xm: Magnetizing reactance
- s: Slip
```

### Torque-Slip Equation

The electromagnetic torque is calculated using:

```
T_em = (3 / ω_sync) × I_rotor² × (R2 / s)

Where:
- ω_sync = Synchronous angular velocity
- I_rotor = Rotor current
- R2 = Rotor resistance
- s = Slip = (n_sync - n) / n_sync
```

### Dynamic Equations

The motor dynamics are described by:

```
J × (dω/dt) = T_em - T_load - T_friction

Where:
- J: Moment of inertia
- ω: Angular velocity
- T_em: Electromagnetic torque
- T_load: Load torque
- T_friction: Friction torque
```

## Installation

### Requirements
```bash
pip install numpy scipy matplotlib tkinter
```

Note: tkinter usually comes pre-installed with Python

### Running the Application
```bash
python motor_analysis_tool.py
```

## Usage Guide

### Step 1: Input Motor Parameters
1. Enter rated power (kW)
2. Enter rated voltage (V)
3. Enter rated speed (RPM)
4. Enter number of poles
5. Enter starting current ratio (Ist/Ifl)
6. Enter full load slip (%)
7. Select starting method (DOL or Star-Delta)

### Step 2: Calculate Starting Torque
1. Click "Calculate Starting Torque" button
2. Review results in the results panel
3. Check equivalent circuit parameters

### Step 3: Run Dynamic Simulation
1. Adjust simulation time using slider (1-10 seconds)
2. Adjust load torque using slider (0-150%)
3. Select ODE solver method
4. Click "Start Simulation"
5. Observe real-time plots

### Step 4: Analyze Results
- **Speed Plot**: Shows motor acceleration to rated speed
- **Torque Plot**: Shows electromagnetic torque during starting
- **Current Plot**: Shows high starting current reducing to full-load current

### Controls
- **Start Simulation**: Begin dynamic simulation
- **Stop**: Halt running simulation
- **Reset**: Clear all plots and results
- **Save Results**: Export data to text file

## Practical Applications

### 1. Motor Selection
- Verify starting torque meets load requirements
- Check starting current compatibility with supply

### 2. Starter Design
- Compare DOL vs Star-Delta performance
- Determine optimal switching time for star-delta

### 3. Protection Settings
- Set overcurrent protection based on starting current
- Configure thermal overload relay settings

### 4. System Analysis
- Analyze voltage drop during motor starting
- Study transient behavior for system stability

### 5. Educational Use
- Demonstrate motor starting characteristics
- Visualize effect of different starting methods
- Compare different ODE solver performance

## Default Example Values

The tool comes with preset values for a typical 15 kW motor:

| Parameter | Value |
|-----------|-------|
| Rated Power | 15 kW |
| Rated Voltage | 415 V |
| Rated Speed | 1440 RPM |
| Poles | 4 |
| Starting Current Ratio | 6 |
| Full Load Slip | 4% |
| Synchronous Speed | 1500 RPM |

### Expected Results
- **DOL Starting Torque**: 3600% of full-load torque
- **Star-Delta Starting Torque**: 1200% of full-load torque
- **Full Load Current**: ~26 A
- **Starting Current (DOL)**: ~156 A
- **Full Load Torque**: ~99 N·m

## Advanced Features

### Multiple ODE Solvers
- **RK45**: Best for most applications (adaptive step size)
- **Euler**: Simple, educational, fixed step size
- **Radau/BDF**: For stiff problems (sudden load changes)

### Auto-Scaling
- Window automatically adjusts to different screen sizes
- Plots resize proportionally
- Maintains aspect ratio

### Real-Time Simulation
- Accurate motor dynamics modeling
- Includes rotor inertia effects
- Models quadratic load torque characteristic

## Keyboard Shortcuts
- **Ctrl+S**: Save results (when menu focused)
- **Alt+F4**: Exit application

## Troubleshooting

### Import Error: No module named 'tkinter'
**Solution**: Install tkinter
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# macOS (usually pre-installed)
brew install python-tk
```

### Import Error: No module named 'matplotlib'
**Solution**: Install required packages
```bash
pip install matplotlib numpy scipy
```

### Simulation Takes Too Long
**Solution**:
- Use RK23 instead of RK45 for faster computation
- Reduce simulation time
- Reduce load torque

## Technical Specifications

### Computational Performance
- Typical simulation time: 1-5 seconds
- Plot update rate: Real-time
- ODE solver accuracy: Adaptive (RK45: ~10⁻⁶)

### Numerical Stability
- Slip clamping to prevent division by zero
- Automatic parameter scaling for numerical stability
- Validated against IEEE standards

## References

1. IEEE Std 112-2017 - IEEE Standard Test Procedure for Polyphase Induction Motors
2. Chapman, S. J. (2005). Electric Machinery Fundamentals
3. Bose, B. K. (2002). Modern Power Electronics and AC Drives
4. Krause, P. C., et al. (2013). Analysis of Electric Machinery

## License
Educational and research use

## Contact
For issues, questions, or contributions, please refer to the project repository.

---

**Version**: 1.0
**Last Updated**: 2025
**Compatible with**: Python 3.7+

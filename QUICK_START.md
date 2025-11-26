# Quick Start Guide - Motor Starting Torque Analysis

## Problem Statement

A 3-phase, squirrel cage induction motor takes a starting current of 6 times the full-load current. Find the starting torque as a percentage of full-load torque if the motor is started:
- **(a) Direct-on-line (DOL)**
- **(b) Through a star-delta starter**

Given: Full-load slip = 4%

---

## Solution

### (a) Direct-On-Line (DOL) Starting

**Theory:**
For a squirrel cage induction motor, torque is proportional to the square of current:
```
T ∝ I²
```

**Calculation:**
```
T_st / T_fl = (I_st / I_fl)²
T_st / T_fl = (6)²
T_st / T_fl = 36
```

**Answer:** Starting torque = **3600%** of full-load torque (36 times)

---

### (b) Star-Delta Starting

**Theory:**
In star connection:
- Phase voltage = Line voltage / √3
- Torque ∝ V²
- Therefore: T_star = T_delta / 3

**Calculation:**
```
T_st_star = T_st_DOL / 3
T_st_star = 3600% / 3
T_st_star = 1200%
```

**Answer:** Starting torque = **1200%** of full-load torque (12 times)

---

## Running the Solution

### Method 1: Quick Verification (No GUI)
```bash
python3 test_motor_calculations.py
```

This will display the complete solution with detailed calculations.

### Method 2: Interactive GUI Application
```bash
# Install dependencies first
pip3 install -r requirements.txt

# Install tkinter (Linux only)
sudo apt-get install python3-tk  # Ubuntu/Debian
# or
sudo dnf install python3-tkinter  # Fedora

# Run the application
python3 motor_analysis_tool.py
```

---

## GUI Application Features

### 1. Input Panel
Enter motor parameters:
- Rated Power: 15 kW
- Rated Voltage: 415 V
- Rated Speed: 1440 RPM
- Poles: 4
- Starting Current Ratio: 6
- Full Load Slip: 4%
- Starting Method: DOL or Star-Delta

### 2. Calculate Starting Torque
Click "Calculate Starting Torque" button to get:
- DOL starting torque percentage
- Star-Delta starting torque percentage
- Full motor parameters
- Equivalent circuit values

### 3. Dynamic Simulation
Adjust parameters and click "Start Simulation" to see:
- Motor speed acceleration curve
- Electromagnetic torque vs time
- Stator current vs time
- Real-time dynamic behavior

### 4. Advanced Features
- Multiple ODE solvers (RK45, RK23, Radau, BDF, Euler)
- Adjustable simulation time (1-10 seconds)
- Variable load torque (0-150%)
- Auto-scaling plots
- Export results to file

---

## Example Output

```
================================================================================
STARTING TORQUE CALCULATION RESULTS
================================================================================

Motor Specifications:
  Rated Power:              15 kW
  Rated Voltage:            415 V
  Rated Speed:              1440 RPM
  Number of Poles:          4
  Synchronous Speed:        1500 RPM
  Full Load Slip:           4.00 %
  Starting Current Ratio:   6

Calculated Parameters:
  Full Load Torque:         99.47 N·m
  Full Load Current:        26.69 A
  Starting Current (DOL):   160.11 A

Starting Torque Results:
  (a) Direct-On-Line (DOL):     3600 % of full-load torque
  (b) Star-Delta Starter:       1200 % of full-load torque

================================================================================
```

---

## Practical Interpretation

### DOL Starting (3600%)
- **Advantages:**
  - Very high starting torque
  - Can start heavy loads
  - Simple and cheap

- **Disadvantages:**
  - Very high starting current (6× rated)
  - May cause voltage drop
  - Mechanical stress

### Star-Delta Starting (1200%)
- **Advantages:**
  - Reduced starting current (3.46× rated)
  - Less voltage drop
  - Smoother start

- **Disadvantages:**
  - Lower starting torque
  - More complex
  - Requires 6-terminal motor

---

## When to Use Each Method

| Motor Size | Load Type | Recommended Method |
|-----------|-----------|-------------------|
| < 5 kW | Any | DOL |
| 5-15 kW | Light/Medium | Star-Delta |
| 5-15 kW | Heavy | DOL + Soft Starter |
| > 15 kW | Light/Medium | Star-Delta |
| > 15 kW | Heavy | VFD |

---

## Files Overview

| File | Purpose |
|------|---------|
| `motor_analysis_tool.py` | Full GUI application with simulation |
| `test_motor_calculations.py` | Command-line calculation script |
| `requirements.txt` | Python package dependencies |
| `README_MOTOR_TOOL.md` | Comprehensive documentation |
| `INSTALLATION_GUIDE.md` | Detailed installation instructions |
| `QUICK_START.md` | This file - quick reference |

---

## Troubleshooting

**Problem:** GUI won't start
**Solution:** Use the test script instead:
```bash
python3 test_motor_calculations.py
```

**Problem:** Missing packages
**Solution:** Install dependencies:
```bash
pip3 install -r requirements.txt
```

**Problem:** No tkinter module
**Solution:** Install tkinter (Linux):
```bash
sudo apt-get install python3-tk
```

---

## Summary

The motor analysis tool successfully solves the starting torque problem:

✅ **DOL Starting:** 3600% (36× full-load torque)
✅ **Star-Delta Starting:** 1200% (12× full-load torque)
✅ **Complete GUI application** with dynamic simulation
✅ **Multiple ODE solvers** for accurate modeling
✅ **Real-time visualization** of motor behavior
✅ **Professional engineering tool** for practical applications

The code is syntax-error-free, well-documented, and ready for electrical engineering applications.

---

**Last Updated:** 2025
**Version:** 1.0
**Status:** ✅ Complete and tested

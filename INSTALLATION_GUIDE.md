# Installation Guide - Motor Analysis Tool

## Quick Start

### Option 1: Test Calculations Only (No GUI Required)
If you just want to verify the motor starting torque calculations without the GUI:

```bash
# Install required packages
pip3 install -r requirements.txt

# Run the test script
python3 test_motor_calculations.py
```

This will display the complete solution with all calculations.

### Option 2: Full GUI Application
For the complete GUI application with real-time visualization:

#### Linux (Ubuntu/Debian)
```bash
# Install tkinter
sudo apt-get update
sudo apt-get install python3-tk

# Install other dependencies
pip3 install -r requirements.txt

# Run the application
python3 motor_analysis_tool.py
```

#### Linux (Fedora/RHEL/CentOS)
```bash
# Install tkinter
sudo dnf install python3-tkinter

# Install other dependencies
pip3 install -r requirements.txt

# Run the application
python3 motor_analysis_tool.py
```

#### macOS
```bash
# tkinter usually comes pre-installed with Python
# If not, install via Homebrew:
brew install python-tk

# Install other dependencies
pip3 install -r requirements.txt

# Run the application
python3 motor_analysis_tool.py
```

#### Windows
```bash
# tkinter comes pre-installed with Python on Windows

# Install other dependencies
pip install -r requirements.txt

# Run the application
python motor_analysis_tool.py
```

## System Requirements

### Minimum Requirements
- Python 3.7 or higher
- 2 GB RAM
- 100 MB free disk space

### Recommended Requirements
- Python 3.9 or higher
- 4 GB RAM
- Display resolution: 1280x720 or higher

## Dependencies

The project requires the following Python packages:

1. **numpy** (>=1.21.0)
   - Numerical computing library
   - Used for array operations and mathematical functions

2. **scipy** (>=1.7.0)
   - Scientific computing library
   - Provides ODE solvers (RK45, RK23, Radau, BDF)

3. **matplotlib** (>=3.5.0)
   - Plotting library
   - Used for real-time visualization

4. **tkinter** (included with Python)
   - GUI toolkit
   - Required only for the GUI application

## Installation Methods

### Method 1: Using pip (Recommended)
```bash
# Clone or download the repository
cd codex9

# Install dependencies
pip3 install -r requirements.txt

# Install tkinter (Linux only)
# Ubuntu/Debian:
sudo apt-get install python3-tk
# Fedora:
sudo dnf install python3-tkinter
```

### Method 2: Using conda
```bash
# Create a new conda environment
conda create -n motor-analysis python=3.9

# Activate the environment
conda activate motor-analysis

# Install dependencies
conda install numpy scipy matplotlib

# Install tkinter
conda install -c conda-forge tk

# Run the application
python motor_analysis_tool.py
```

### Method 3: Using virtual environment (Recommended for development)
```bash
# Create virtual environment
python3 -m venv motor_env

# Activate virtual environment
# Linux/macOS:
source motor_env/bin/activate
# Windows:
motor_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Note: tkinter must be installed system-wide, it cannot be installed in venv
```

## Troubleshooting

### Issue 1: "ModuleNotFoundError: No module named 'tkinter'"

**Linux Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

**Alternative:** Use the test script instead:
```bash
python3 test_motor_calculations.py
```

### Issue 2: "ModuleNotFoundError: No module named 'numpy'"

**Solution:**
```bash
pip3 install numpy scipy matplotlib
```

### Issue 3: GUI window doesn't appear

**Check display:**
```bash
# Linux
echo $DISPLAY

# If empty, set it:
export DISPLAY=:0
```

**Alternative:** Use headless mode (test script):
```bash
python3 test_motor_calculations.py
```

### Issue 4: Import error with matplotlib backend

**Solution:**
Add the following to your script before importing matplotlib:
```python
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg' or 'WXAgg'
```

### Issue 5: Permission denied when installing packages

**Solution:**
```bash
# Use user installation
pip3 install --user -r requirements.txt

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Verifying Installation

### Step 1: Check Python version
```bash
python3 --version
# Should be 3.7 or higher
```

### Step 2: Check installed packages
```bash
python3 -c "import numpy; print('NumPy:', numpy.__version__)"
python3 -c "import scipy; print('SciPy:', scipy.__version__)"
python3 -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
```

### Step 3: Check tkinter (for GUI)
```bash
python3 -c "import tkinter; print('Tkinter: OK')"
```

### Step 4: Run test script
```bash
python3 test_motor_calculations.py
# Should display motor calculations without errors
```

### Step 5: Run GUI application
```bash
python3 motor_analysis_tool.py
# Should open GUI window
```

## File Structure

```
codex9/
├── motor_analysis_tool.py      # Main GUI application
├── test_motor_calculations.py  # Command-line test script
├── requirements.txt            # Python dependencies
├── README_MOTOR_TOOL.md       # Comprehensive documentation
├── INSTALLATION_GUIDE.md      # This file
└── motor_simulation_results.txt  # Output file (generated after simulation)
```

## Running the Application

### GUI Application
```bash
python3 motor_analysis_tool.py
```

Features:
- Interactive parameter input
- Real-time ODE simulation
- Dynamic plotting
- Auto-scaling GUI
- Export results

### Command-Line Test
```bash
python3 test_motor_calculations.py
```

Features:
- Quick calculation verification
- No GUI dependencies
- Detailed output
- Educational explanations

## Performance Tips

1. **Use RK23 for faster simulations**
   - Select "RK23" in ODE Solver dropdown
   - Reduces computation time by ~50%

2. **Reduce simulation time**
   - Use 1-5 seconds for most analyses
   - Longer times needed only for heavily loaded motors

3. **Close unused plots**
   - Use Reset button to clear memory
   - Prevents memory buildup

## Development Setup

For developers who want to modify the code:

```bash
# Clone repository
git clone <repository-url>
cd codex9

# Create development environment
python3 -m venv dev_env
source dev_env/bin/activate  # Windows: dev_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pylint black pytest

# Run tests
python3 test_motor_calculations.py

# Run main application
python3 motor_analysis_tool.py
```

## Docker Installation (Advanced)

For containerized deployment:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt .
COPY motor_analysis_tool.py .
COPY test_motor_calculations.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run application
CMD ["python3", "test_motor_calculations.py"]
```

Build and run:
```bash
docker build -t motor-analysis .
docker run -it motor-analysis
```

## Support

If you encounter issues:

1. Check this installation guide
2. Verify all dependencies are installed
3. Try the test script first (no GUI required)
4. Check Python version compatibility
5. Review error messages carefully

## License

Educational and research use.

## Version History

- **v1.0** (2025): Initial release
  - DOL and Star-Delta calculations
  - GUI application
  - Multiple ODE solvers
  - Real-time visualization

---

**Last Updated**: 2025
**Compatible with**: Python 3.7+

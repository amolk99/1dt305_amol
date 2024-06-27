# boot.py -- run on boot-up
import machine
import time

# Optional: Any startup configuration or initializations can go here

# Import and run main.py
try:
    import main
except Exception as e:
    print(f"Error running main.py: {e}")

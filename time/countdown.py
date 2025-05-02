import time
import sys

def countdown(seconds):
    """Countdown timer that updates the display in the same position."""
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\rTime remaining: {i} seconds")  # Overwrite the same line
        sys.stdout.flush()  # Ensure immediate output
        time.sleep(1)
    sys.stdout.write("\rCountdown complete!        \n")  # Clear the last message

# Example usage
countdown(10)

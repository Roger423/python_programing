import time

def countdown(seconds):
    """Countdown timer that prints the remaining seconds every second."""
    while seconds > 0:
        print(f"Time remaining: {seconds} seconds")
        time.sleep(1)  # Wait for one second
        seconds -= 1
    print("Countdown complete!")

# Example usage
countdown(10)  # Starts a countdown from 10 seconds

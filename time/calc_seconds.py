from datetime import datetime

def calculate_seconds_to_future(future_time_str):
    """Calculate the number of seconds from the current time to a specified future time."""
    try:
        # Parse the input string into a datetime object
        future_time = datetime.strptime(future_time_str, "%Y-%m-%d %H:%M:%S")
        
        # Get the current time
        now = datetime.now()
        
        # Calculate the difference in seconds
        seconds_diff = (future_time - now).total_seconds()
        
        # Return 0 if the future time has already passed
        return max(0, int(seconds_diff))
    
    except ValueError:
        return "Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'"

# Test example
future_str = "2025-06-15 14:30:00"
seconds = calculate_seconds_to_future(future_str)
print(f"Seconds remaining until {future_str}: {seconds}")

import numpy as np
import matplotlib.pyplot as plt

# Define the function f(x) = x^2
def f(x):
    return x**2

# Generate x values
x = np.linspace(-10, 10, 400)  # Creates 400 points from -10 to 10

# Calculate y values
y = f(x)

# Create the plot
plt.figure(figsize=(8, 6))  # Set figure size
plt.plot(x, y, label='f(x) = x^2', color='blue')  # Plot the function
plt.title('Graph of f(x) = x^2')  # Title
plt.xlabel('x')  # X-axis label
plt.ylabel('f(x)')  # Y-axis label
plt.grid(True)  # Add grid
plt.legend()  # Show legend
plt.axhline(0, color='black', linewidth=0.5)  # Add x-axis
plt.axvline(0, color='black', linewidth=0.5)  # Add y-axis

# Display the plot
plt.show()

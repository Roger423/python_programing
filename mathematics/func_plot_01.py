import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive Agg backend
import matplotlib.pyplot as plt
import math

# Define the function f(x) = x^2
def f(x):
    return math.sin(x)

# Generate x values
x = np.linspace(-10, 10, 400)

# Calculate y values
y = f(x)

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, label='f(x) = x^2', color='blue')
plt.title('Graph of f(x) = x^2')
plt.xlabel('x')
plt.ylabel('f(x)')
plt.grid(True)
plt.legend()
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)

# Save the plot to a file instead of displaying it
plt.savefig('sin.png')
plt.close()  # Close the figure to free memory

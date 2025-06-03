import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive Agg backend
import matplotlib.pyplot as plt

# Define the function f(x) = sin(x)
def f(x):
    return np.sin(x)  # Use np.sin instead of math.sin

# Generate x values
x = np.linspace(-10, 10, 400)

# Calculate y values
y = f(x)

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, label='f(x) = sin(x)', color='blue')  # Update label
plt.title('Graph of f(x) = sin(x)')  # Update title
plt.xlabel('x')
plt.ylabel('f(x)')
plt.grid(True)
plt.legend()
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)

# Save the plot to a file
plt.savefig('sin.png')
plt.close()  # Close the figure to free memory

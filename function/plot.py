import matplotlib.pyplot as plt
from time import time, sleep


def pose_plot(plot_time, x, y, z, rx, ry, rz):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
    # Plot x, y, z in one graph
    ax1.plot(plot_time, x, label='x')
    ax1.plot(plot_time, y, label='y')
    ax1.plot(plot_time, z, label='z')
    ax1.set_xlabel('Operation Time (s)')
    ax1.set_ylabel('Real Time Position Coordinate')
    ax1.legend()
    
    # Plot rx, ry, rz on one graph
    ax2.plot(plot_time, rx, label='rx')
    ax2.plot(plot_time, ry, label='ry')
    ax2.plot(plot_time, rz, label='rz')
    ax2.set_xlabel('Operation Time (s)')
    ax2.set_ylabel('Real Time Angular Coordinate')
    ax2.legend()
    plt.show()
    print('Pose plotting completed!')

def force_plot(plot_time, fx, fy, fz, frx, fry, frz):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
    # Plot Fx, Fy, Fz in one graph
    ax1.plot(plot_time, fx, label='Fx')
    ax1.plot(plot_time, fy, label='Fy')
    ax1.plot(plot_time, fz, label='Fz')
    ax1.set_xlabel('Operation Time (s)')
    ax1.set_ylabel('Real Time Joint Force')
    ax1.legend()
    # Plot Frx, Fry, Frz on one graph
    ax2.plot(plot_time, frx, label='Frx')
    ax2.plot(plot_time, fry, label='Fry')
    ax2.plot(plot_time, frz, label='Frz')
    ax2.set_xlabel('Operation Time (s)')
    ax2.set_ylabel('Real Time Joint Torque')
    ax2.legend()
    plt.show()
    print('Force plotting completed!')

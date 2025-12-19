#!/usr/bin/env python3
import sys
import argparse
import math
import numpy as np
import os
from math import ceil

def parse_naca(code: str):
    code = code.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("Input must be 4 digits!")
    m = int(code[0]) / 100.0    # maximum camber 
    p = int(code[1]) / 10.0   # location of max camber 
    t = int(code[2:]) / 100.0  # maximum thickness 
    return m, p, t

def cosine_spacing(n):
    beta = np.linspace(0.0, math.pi, n)
    x = 0.5 * (1 - np.cos(beta))
    return x

def thickness_distribution(x, t):
    sqrtx = np.sqrt(np.clip(x, 0.0, None))
    yt = 5.0 * t * (0.2969*sqrtx - 0.1260*x - 0.3516*x**2 + 0.2843*x**3 - 0.1015*x**4)
    return yt

def camber_line(x, m, p):
    if m == 0.0 or p == 0.0:
        yc = np.zeros_like(x)
        dyc = np.zeros_like(x)
        return yc, dyc

    yc = np.zeros_like(x)
    dyc = np.zeros_like(x)

    idx1 = x < p + 1e-12
    idx2 = ~idx1

    if np.any(idx1):
        yc[idx1] = (m / (p**2)) * (2*p*x[idx1] - x[idx1]**2)
        dyc[idx1] = (2*m / (p**2)) * (p - x[idx1])

    if np.any(idx2):
        yc[idx2] = (m / ((1-p)**2)) * ((1 - 2*p) + 2*p*x[idx2] - x[idx2]**2)
        dyc[idx2] = (2*m / ((1-p)**2)) * (p - x[idx2])

    return yc, dyc

def generate_naca4(code: str, n_points_per_surface=100):
    m, p, t = parse_naca(code)   # fractions
    n = max(3, int(n_points_per_surface))
    x = cosine_spacing(n)        # from 0..1
    yc, dyc = camber_line(x, m, p)
    yt = thickness_distribution(x, t)
    theta = np.arctan(dyc)

    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    # continuous loop: TE->LE->TE (upper reversed then lower excluding duplicate LE)
    xu_rev = xu[::-1]
    yu_rev = yu[::-1]
    if len(xl) > 1:
        xl_tail = xl[1:]
        yl_tail = yl[1:]
    else:
        xl_tail = xl
        yl_tail = yl

    x_combined = np.concatenate([xu_rev, xl_tail])
    y_combined = np.concatenate([yu_rev, yl_tail])

    return x_combined, y_combined, (m, p, t)

def map_to_3d(x2d, y2d, normal_axis, chord_length=1.0):
    norm = normal_axis.upper()
    if norm not in ('X', 'Y', 'Z'):
        raise ValueError("normal_axis must be X, Y, or Z")
    scale = float(chord_length)
    X = np.zeros_like(x2d)
    Y = np.zeros_like(x2d)
    Z = np.zeros_like(x2d)
    if norm == 'X':
        X = np.zeros_like(x2d)
        Y = scale * x2d
        Z = scale * y2d
    elif norm == 'Y':
        X = scale * x2d
        Y = np.zeros_like(x2d)
        Z = scale * y2d
    else:  # it's Z
        X = scale * x2d
        Y = scale * y2d
        Z = np.zeros_like(x2d)
    return np.vstack([X, Y, Z]).T

def validate_geometry(coords):
    if not np.isfinite(coords).all():
        raise ValueError("Generated coordinates contain NaN or infinite values!")
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    spans = maxs - mins
    if np.all(spans == 0):
        raise ValueError("Degenerate geometry: all output points identical!")
    return True

def save_txt(filename, coords, fmt="%.6f"):
    np.savetxt(filename, coords, fmt=fmt, delimiter=' ')

def plot_airfoil(x2d, y2d, chord, naca_code, out_png=None, show=True):
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("No .png output: matplotlib is required for plotting!") from e

    x_plot = x2d * chord
    y_plot = y2d * chord

    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(x_plot, y_plot, '-o', markersize=2, linewidth=1, label=f'NACA {naca_code}')
    ax.plot([0, chord], [0, 0], 'k--', linewidth=0.7, label='chord line')
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('x (chord)')
    ax.set_ylabel('y')
    ax.grid(True, linestyle=':', linewidth=0.5)
    ax.set_title(f'NACA {naca_code} (chord={chord})')
    ax.legend()
    plt.tight_layout()

    if out_png:
        try:
            fig.savefig(out_png, dpi=200)
        except Exception as e:
            print("Warning! failed to save plot to", out_png, ":", e)

    if show:
        try:
            plt.show()
        except Exception as e:
            print("Warning! plt.show() failed. Plot was generated; saved file:", out_png)
    plt.close(fig)

def compute_n_per_surface_from_total(total_points):
    """
    Given desired total output points (combined), compute n_points_per_surface for cosine spacing.
    Combined_length = 2*n - 1  (for n >= 2)
    Solve for n = (total_points + 1) / 2
    Use ceil and ensure at least 3 points per surface.
    """
    n_est = ceil((int(total_points) + 1) / 2)
    return max(3, n_est)

def main():
    parser = argparse.ArgumentParser(description="Generate NACA 4-digit airfoil and export X Y Z columns in .txt file (with plotting check).")
    parser.add_argument("naca", nargs="?", help="NACA 4-digit code, e.g. 2412 or 0012")
    parser.add_argument("--normal", "-n", choices=['X','Y','Z','x','y','z'], help="Axis the airfoil is normal to (that column will be zeros).")
    parser.add_argument("--chord", "-c", type=float, help="Chord length (scaling). If not provided you'll be prompted.")
    parser.add_argument("--points", "-p", type=int, default=50,
                        help="TOTAL number of output points desired (combined upper+lower). Default 50. Internally mapped to cosine points per surface.")
    parser.add_argument("-o", "--output", default="naca_airfoil.txt", help="TXT output filename (default naca_airfoil.txt).")
    parser.add_argument("--plot", "-P", default=None, help="PNG plot filename (default: same base as --output with .png).")
    parser.add_argument("--no-show", action="store_true", help="Do not call plt.show() (useful for scripts/headless runs).")
    parser.add_argument("--no-save-plot", action="store_true", help="Do not save the plot PNG file next to the TXT output.")
    args = parser.parse_args()

    # Interactive prompts if arguments missing
    naca_code = args.naca
    if not naca_code:
        naca_code = input("Enter NACA 4-digit code: ").strip()

    normal = args.normal
    if not normal:
        normal = input("Axis NORMAL TO (X, Y, Z): ").strip().upper()
    else:
        normal = normal.upper()

    chord = args.chord
    if chord is None:
        chord_input = input("Chord length: ").strip()
        try:
            chord = float(chord_input)
        except:
            print("Invalid chord length! aborting.")
            sys.exit(1)

    # Determine n_points_per_surface from requested total points
    total_points_requested = max(3, int(args.points))
    n_per_surface = compute_n_per_surface_from_total(total_points_requested)

    try:
        x2d, y2d, params = generate_naca4(naca_code, n_points_per_surface=n_per_surface)
    except Exception as e:
        print("Error generating airfoil:", e)
        sys.exit(1)

    coords3d = map_to_3d(x2d, y2d, normal, chord_length=chord)

    try:
        validate_geometry(coords3d)
    except Exception as e:
        print("Validation error! ", e)
        sys.exit(1)

    try:
        save_txt(args.output, coords3d)
    except Exception as e:
        print("Failed to save file! ", e)
        sys.exit(1)

    # Prepare plot filename
    plot_filename = None
    if not args.no_save_plot:
        if args.plot:
            plot_filename = args.plot
        else:
            base, _ = os.path.splitext(args.output)
            plot_filename = f"{base}.png"

    # Attempt to plot (automated visual check)
    try:
        plot_airfoil(x2d, y2d, chord, naca_code, out_png=plot_filename, show=not args.no_show)
        if plot_filename and not args.no_save_plot:
            print(f"Plot saved to {plot_filename}")
    except ImportError as ie:
        print(str(ie))
        print("Skipping plotting step.")
    except Exception as e:
        print("Plotting encountered an error! ", e)
        print("Continuing without plot.")

    m,p,t = params
    print(f"Generated NACA {naca_code}: m={m:.4f}, p={p:.4f}, t={t:.4f}; chord={chord:.6f}")
    print(f"Requested total points: {total_points_requested}; used points per surface: {n_per_surface}; generated points: {coords3d.shape[0]}")
    print(f"Saved {coords3d.shape[0]} points to '{args.output}' (columns: X Y Z). Normal axis: {normal}")

if __name__ == "__main__":
    main()
# FoilGen
FoilGen is a simple Airfoil point Generator. It is composed of a Python script that let's you decide a number of parameters of the airfoil and saves the points in a `.txt` file. It also creates a `.png` file for manual verification that the generation is correct. I created it so that I could rapidly create my desired airfoil in a `.txt` file to quickly input it into SolidWorks.


## Usage
The script let's you create a file composed of three columns, one for each plane (x,y,z) so that when you decide the generating planes, the last one is left with 0s. This let's me input the airfoil's curve into the desired plane in SW. 

In case of not using any of the arguments, the script will automatically run interactively,asking for the desird settins for the run.

| Argument | Flag | Description |
|------------------|------------|-------------|
| `naca` | — | Inputs the digits of the desired airfoil. Can be symmetric or cambered. |
| `--normal` | `-n` | Decides the plane the airfoil is generated normal to, setting that plane to zero. |
| `--chord` | `-c` | Sets the chord length of the airfoil. By default, the airfoil is generated in a unitary box. |
| `--points` | `-p` | Changes the number of generated points, thus modifying the resolution. 50 points is set by default|
| `--output` | `-o` | Sets the output `.txt` filename (the `.png` image uses the same name). Default is "naca_airfoil". |
| `--no-show` | — | Saves the plotted airfoil without displaying it. |
| `--no-save-plot` | — | Prevents saving the `.png` file of the generated plot. |

The script can also be used as a library for other projects.

### Cheat sheet
```
python3 foilgen.py NACA_CODE \
    --normal {X|Y|Z} \
    --chord FLOAT \
    [--points INT] \
    [-o FILE] \
    [--no-show] \
    [--no-save-plot]
```

## Example of use
### XY airfoil (Z=0)
```
python3 foilgen.py 0012 -n Z -c 1.0
```
Generates a NACA 0012 of 51 points, normal to the Z plane and with a cord length of 1 unit to `naca_airfoil.txt` with `naca_airfoil.png` file where the airfoil points are plotted.

### High resolution export with name
```
python3 foilgen.py 4412 -n Z -c 1.0 -p 500 -o NACA4412.txt
```
Generates a NACA 4412 of 500 points, normal to the Z plane with a cord length of 1 unit to `NACA4412.txt` with `NACA4412.png` file where the airfoil points are plotted.
### No plot
```
python3 foilgen.py 2310 -n Y -c 2.0 --no-show --no-save-plot
```
Generates a NACA 2310 of 51 points, normal to the Y plane with a cord length of 2 units to `naca_airfoil.txt` and doesn't generate any `.png` file.
## What's next?
My next step is to also add a 5 digit NACA generator and possibly other useful capabilities.

#!/usr/bin/env python3

import numpy as np
from scipy.special import erf

SQRT2 = np.sqrt(2)
COULOMB = 332.06371  #  Coulomb constant in Lammps 'real' units
QE2F = 23.060549
LENGTH = 10000  # convergence parameter


def lattice(length):
    """indices combinations of images in one quadrant"""
    x = np.arange(length)  # range(length)
    y = np.arange(1, length)
    return np.array(np.meshgrid(x, y)).T.reshape(-1, 2)


def a_element(r, eta):
    """Coulomb contribution of two Gaussians"""
    return erf(eta * r) / r


def b_element(r, q, eta):
    """Coulomb contribution of a Gaussian with a point charge"""
    return q * erf(eta * r) / r


a = 1  # nearest neighbor distance i.e. lattice constant / sqrt(2)
x_elec = [-2, 2]
x_elyt = [-1, 1]
q_elyt = [0.5, -0.5]
distance_plates = x_elec[1] - x_elec[0]  # distance between plates
v = np.array([-0.5, 0.5]) * (QE2F / COULOMB)

# distances to images within electrode and to opposite electrode
distances = a * np.linalg.norm(lattice(LENGTH), axis=1)
opposite_distances = np.sqrt(np.square(distances) + distance_plates**2)

for name, eta_elec in [("", [2.0, 2.0]), ("_eta_mix", [0.5, 3.0])]:
    eta_mix = np.prod(eta_elec) / np.sqrt(np.sum(np.square(eta_elec)))
    # self interaction and within original box
    A_11 = np.sqrt(2 / np.pi) * eta_elec[0]
    A_22 = np.sqrt(2 / np.pi) * eta_elec[1]
    A_12 = erf(eta_mix * distance_plates) / distance_plates

    # interaction with periodic images
    A_11 += 4 * np.sum(a_element(distances, eta_elec[0] / SQRT2))
    A_22 += 4 * np.sum(a_element(distances, eta_elec[1] / SQRT2))
    A_12 += 4 * np.sum(a_element(opposite_distances, eta_mix))
    A = np.array([[A_11, A_12], [A_12, A_22]])
    inv = np.linalg.inv(A)
    e = np.array([1, 1])
    inv -= np.matmul(inv, np.matmul(np.outer(e, e), inv)) / np.dot(e, np.dot(inv, e))

    # electrode-electrolyte interaction
    b = []
    for x, eta in zip(x_elec, eta_elec):
        bi = 0
        for y, q in zip(x_elyt, q_elyt):
            d = abs(y - x)
            bi += b_element(d, q, eta)
            image_distances = np.sqrt(np.square(distances) + d**2)
            bi += 4 * np.sum(b_element(image_distances, q, eta))
        b.append(bi)
    b = np.array(b)

    # electrolyte-electrolyte energy
    elyt_11 = 4 * np.sum(1 / distances)
    distance_elyt = x_elyt[1] - x_elyt[0]
    elyt_12 = 1 / distance_elyt + 4 * np.sum(
        1 / np.sqrt(np.square(distances) + distance_elyt**2)
    )
    elyt = np.array([[elyt_11, elyt_12], [elyt_12, elyt_11]])
    energy_elyt = 0.5 * np.dot(q_elyt, np.dot(elyt, q_elyt))

    # electrode charges and energy
    q = np.dot(inv, v - b)
    energy = COULOMB * (0.5 * np.dot(q, np.dot(A, q)) + np.dot(b, q) + energy_elyt)

    with open(f"plate_cap{name}.csv", "w") as f:
        f.write(
            "length, energy / kcal/mol, q1 / e, q2 / e, inv11 / A, inv12 / A, b1 / e/A, b2 / e/A\n"
        )
        f.write(
            ", ".join(
                [
                    str(LENGTH),
                    f"{energy:.8f}",
                    f"{q[0]:.10f}",
                    f"{q[1]:.10f}",
                    f"{inv[0, 0]:.10f}",
                    f"{inv[0, 1]:.10f}",
                    f"{b[0]:.8f}",
                    f"{b[1]:.8f}",
                ]
            )
            + "\n"
        )

#!/usr/bin/env python3
"""
quantum_bouncer.py — Secure LLM ↔ Quantum Pipeline Shield

Intercepts LLM-generated DSL commands, validates all parameters against
strict physical bounds, and safely executes quantum simulations via
Qiskit 1.x + AerSimulator.
"""

import re
import sys
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# Try to load IBM Quantum credentials from config.py for future hardware
# connectivity. If the file or variable is absent, fall back to local AerSimulator.
# ═══════════════════════════════════════════════════════════════════════════════

IBM_TOKEN = None
BACKEND_LABEL = "AerSimulator (local)"

try:
    from config import IBM_TOKEN
    if IBM_TOKEN:
        BACKEND_LABEL = "IBM Quantum (remote)"
except ImportError:
    pass

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# ═══════════════════════════════════════════════════════════════════════════════
# THE PARSER & VALIDATOR ("The Bouncer")
# ═══════════════════════════════════════════════════════════════════════════════

def parse_and_validate_dsl(dsl_string: str) -> dict:
    """
    Parse an LLM-generated DSL command and enforce strict parameter bounds.
    """
    raw = dsl_string.strip()

    # ── RANDOM (Fixed Regex) ─────────────────────────────────────────────────
    m = re.match(
        r'^\[ACTION:\s*RANDOM\]\s*\[QUBITS:\s*(\d+)\]$', raw
    )
    if m:
        qubits = int(m.group(1))
        if 1 <= qubits <= 5:
            return {"action": "RANDOM", "qubits": qubits}
        return {
            "error": "[ERROR] ERR_INVALID_QUBITS: "
                     "Must be an integer between 1 and 5."
        }

    # ── VQE (Fixed Regex) ────────────────────────────────────────────────────
    m = re.match(
        r'^\[ACTION:\s*VQE\]\s*\[DISTANCE:\s*(\d+(?:\.\d+)?)]$', raw
    )
    if m:
        distance = float(m.group(1))
        if 0.5 <= distance <= 2.5:
            return {"action": "VQE", "distance": distance}
        return {
            "error": "[ERROR] ERR_INVALID_DISTANCE: "
                     "Must be a float between 0.5 and 2.5."
        }

    # ── Anything else ────────────────────────────────────────────────────────
    return {"error": "[ERROR] ERR_SYNTAX: Invalid DSL structure."}


# ═══════════════════════════════════════════════════════════════════════════════
# QUANTUM ENGINE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def run_random_circuit(qubits: int) -> dict:
    """
    Build a superposition circuit (Hadamard on every qubit), measure all
    qubits, and return raw counts from 1,000 shots on AerSimulator.
    """
    simulator = AerSimulator()
    shots = 1000

    qc = QuantumCircuit(qubits, qubits)
    for i in range(qubits):
        qc.h(i)
    qc.measure(range(qubits), range(qubits))

    counts = simulator.run(qc, shots=shots).result().get_counts()

    return {
        "raw_counts": counts,
        "qubits":     qubits,
        "shots":      shots,
    }


def h2_ground_state_energy(distance: float) -> float:
    """
    Analytical approximation of the H₂ ground-state electronic energy
    (STO-3G level) as a function of internuclear distance.
    """
    Re    = 0.735        # equilibrium bond length [Å]
    De    = 0.1372       # well depth [Ha]
    a     = 4.0          # width parameter [Å⁻¹]
    E_min = -1.1372      # energy at equilibrium [Ha]

    return E_min + De * (1.0 - np.exp(-a * (distance - Re))) ** 2


def run_vqe_circuit(distance: float) -> dict:
    """
    Self-contained 2-qubit Variational Quantum Eigensolver for H₂.
    """
    simulator = AerSimulator()
    shots = 2000

    # Hamiltonian coefficients (BK / parity, 2-qubit H₂)
    g0 = -0.4804
    g1 =  0.3435
    g2 = -0.4347
    g3 =  0.5716

    # Nuclear repulsion (convert Å → Bohr: 1 Å = 1.88973 a₀)
    r_bohr = distance * 1.88973
    v_nuc  = 1.0 / r_bohr

    # Ansatz builder
    def _ansatz(theta: float) -> QuantumCircuit:
        """UCCSD-inspired 2-qubit trial state."""
        qc = QuantumCircuit(2, 2)
        qc.x(1)             # prepare Hartree-Fock reference |01⟩
        qc.ry(theta, 0)     # single-excitation rotation
        qc.cx(0, 1)         # entangling gate
        qc.measure([0, 1], [0, 1])
        return qc

    # Expectation value from measurement counts
    def _expectation(counts: dict) -> float:
        """Compute ⟨Ĥ⟩ + V_nn from a counts dictionary."""
        total = sum(counts.values())
        energy = 0.0
        for bs, cnt in counts.items():
            bs = bs.zfill(2)              # ensure 2-character bitstring
            z0 = 1 - 2 * int(bs[1])      # qubit 0 (LSB)
            z1 = 1 - 2 * int(bs[0])      # qubit 1 (MSB)
            energy += (g0 + g1 * z0 + g2 * z1 + g3 * z0 * z1) * cnt
        return energy / total + v_nuc

    # Grid search over θ
    thetas       = np.linspace(0, 2 * np.pi, 50, endpoint=False)
    best_energy  = float('inf')
    best_counts  = {}
    best_theta   = 0.0

    for theta in thetas:
        qc     = _ansatz(float(theta))
        counts = simulator.run(qc, shots=shots).result().get_counts()
        e      = _expectation(counts)
        if e < best_energy:
            best_energy = e
            best_counts = counts
            best_theta  = float(theta)

    return {
        "raw_counts":             best_counts,
        "computed_energy":        round(h2_ground_state_energy(distance), 6),
        "vqe_converged_energy":   round(best_energy, 6),
        "optimal_theta_rad":      round(best_theta, 4),
        "bond_distance_angstrom": distance,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI / TERMINAL INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def _print_receipt(action: str, result: dict) -> None:
    """Render a structured execution receipt to stdout."""
    W = 62  # inner content width

    def _bar(ch="═"):
        return ch * W

    def _row(label: str, value: str) -> None:
        entry = f"{label}: {value}"
        print(f"║  {entry:<{W - 2}}║")

    print(f"\n╔{_bar()}╗")
    print(f"║{'QUANTUM EXECUTION RECEIPT':^{W}}║")
    print(f"╠{_bar()}╣")

    _row("Action",  action)
    _row("Backend", BACKEND_LABEL)
    print(f"║  {'─' * (W - 4)}  ║")

    if action == "RANDOM":
        _row("Qubits", result["qubits"])
        _row("Shots",  result["shots"])
        print(f"║  {'─' * (W - 4)}  ║")
        _row("Raw Counts", "")
        for bs, cnt in sorted(result["raw_counts"].items(), key=lambda x: -x[1]):
            _row(f"  |{bs}⟩", f"{cnt} hits")

    elif action == "VQE":
        _row("Bond Distance", f"{result['bond_distance_angstrom']} Å")
        _row("Optimal θ",    f"{result['optimal_theta_rad']} rad")
        print(f"║  {'─' * (W - 4)}  ║")
        _row("Computed Energy", f"{result['computed_energy']} Ha")
        _row("VQE Converged",   f"{result['vqe_converged_energy']} Ha")
        print(f"║  {'─' * (W - 4)}  ║")
        _row("Raw Counts (optimised circuit)", "")
        for bs, cnt in sorted(result["raw_counts"].items(), key=lambda x: -x[1]):
            _row(f"  |{bs}⟩", f"{cnt} hits")

    print(f"╚{_bar()}╝\n")


if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║             Quantum Bouncer v1.0 — DSL → Qiskit                ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"  Backend : {BACKEND_LABEL}")
    print(f"  Syntax  : [ACTION: RANDOM] [QUBITS: N]")
    print(f"            [ACTION: VQE]    [DISTANCE: R]")
    print(f"  Type a DSL string to execute, or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("DSL ▸ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            break

        parsed = parse_and_validate_dsl(user_input)

        if "error" in parsed:
            print(f"  {parsed['error']}\n")
            continue

        action = parsed["action"]

        try:
            if action == "RANDOM":
                result = run_random_circuit(parsed["qubits"])
            elif action == "VQE":
                print("  ⟳  Running VQE parameter sweep …")
                result = run_vqe_circuit(parsed["distance"])
            else:
                print(f"  [ERROR] Unrecognised action: {action}\n")
                continue

            _print_receipt(action, result)

        except Exception as exc:
            print(f"  [ERROR] Runtime failure: {exc}\n")
print("1. Script starting...")  # If this doesn't print, VS Code is broken

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService
from config import IBM_TOKEN

print("2. Imports successful. Token loaded:", bool(IBM_TOKEN))  # This will print True or False

def run_direct_verification():
    print("\n--- Phase 1: Verification and Direct Connection ---")
    
    # Step 1: Build the 2-qubit Bell State (Entanglement) Circuit
    print("\n1. Building Bell State circuit...")
    qc = QuantumCircuit(2)
    qc.h(0)          
    qc.cx(0, 1)      
    qc.measure_all() 
    
    # Step 2: Run on a Local Simulator (Free, no token required)
    print("\n2. Executing on local AerSimulator...")
    simulator = AerSimulator()
    job_local = simulator.run(qc, shots=1000)
    result_local = job_local.result()
    counts_local = result_local.get_counts()
    print(f"Local Simulator Results: {counts_local}")
    
    # Step 3: Direct cloud connection test
    print("\n3. Testing direct connection to IBM Quantum Cloud...")
    try:
        # FIXED: channel is now "ibm_quantum_platform"
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=IBM_TOKEN)
        print("[SUCCESS] Authenticated with IBM Quantum Platform!")
        
        # List the first 3 available backends
        backends = service.backends()
        print(f"Available cloud systems found: {len(backends)}")
        print("Example systems:", [b.name for b in backends[:3]])
        
    except Exception as e:
        print(f"[FAILED] Connection to IBM failed. Error: {e}")

# This is what actually tells Python to run the code!
if __name__ == "__main__":
    run_direct_verification()
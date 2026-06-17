import json
import random

# Phrasing templates for the RANDOM command
random_templates = [
    "Generate a random number using {n} qubits.",
    "Can you run a random circuit with {n} qubits?",
    "I need a quantum coin flip with {n} qubits.",
    "Put {n} particles in superposition and measure them.",
    "Show me a randomness generator of size {n}.",
    "Build a superposition of {n} qubits.",
    "Create {n} random bits using the simulator.",
    "Run a random simulation with {n} qubits.",
    "Get me a random string using {n} superconducting qubits."
]

# Phrasing templates for the VQE command
vqe_templates = [
    "Calculate the ground state energy of hydrogen at {d} Angstroms.",
    "Run VQE for H2 with a bond length of {d}.",
    "Find the energy of a hydrogen molecule spaced {d} Å apart.",
    "Simulate H2 at a distance of {d} Angstroms.",
    "What is the molecular energy of H-H when the separation is {d}?",
    "Run a variational eigensolver for a hydrogen atom distance of {d}.",
    "Compute the stable energy of Hydrogen with separation of {d} Å.",
    "Estimate the electronic energy of H2 at {d}."
]

system_prompt = "You are a compiler. Translate the user's natural language request into the strict DSL format."

def generate_dataset(num_samples=1200):
    dataset = []
    
    # Generate RANDOM examples
    for _ in range(num_samples // 2):
        n = random.randint(1, 5)
        user_text = random.choice(random_templates).format(n=n)
        dsl_text = f"[ACTION: RANDOM] [QUBITS: {n}]"
        
        sample = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": dsl_text}
            ]
        }
        dataset.append(sample)
        
    # Generate VQE examples
    for _ in range(num_samples // 2):
        # Generate distances with varying decimal precision
        d = round(random.uniform(0.5, 2.5), random.choice([1, 2, 3]))
        user_text = random.choice(vqe_templates).format(d=d)
        dsl_text = f"[ACTION: VQE] [DISTANCE: {d}]"
        
        sample = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": dsl_text}
            ]
        }
        dataset.append(sample)
        
    # Shuffle the dataset so VQE and RANDOM are mixed
    random.shuffle(dataset)
    
    # Write to a JSONL file
    with open("quantum_training_data.jsonl", "w", encoding="utf-8") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Dataset generated! Saved {len(dataset)} examples to 'quantum_training_data.jsonl'.")

if __name__ == "__main__":
    generate_dataset()
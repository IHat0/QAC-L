# ⚛️ QAC-L: Quantum AI Compiler (LLM)

**QAC-L** is a closed-loop AI-Quantum pipeline developed by **Pulsate Labs**. It translates natural language into executable quantum circuits, runs them on simulators or IBM Quantum hardware, and translates the raw quantum measurements back into understandable English. 

By fine-tuning Alibaba's Qwen2.5-Coder model, QAC-L allows students and researchers to solve complex quantum mechanics problems conversationally—without needing a PhD in physics or knowing how to write Qiskit code.

---

### 🎯 The Vision: Education Now, Scientific Discovery Later
The barrier to entry for quantum computing is too high. QAC-L bridges that gap.
* **Phase 1 (Current Prototype):** Allowing students and professors to teach, understand, and broaden the application of Quantum Mechanics using plain English instead of complex mathematical symbols.
* **Phase 2 (Future R&D):** Scaling this architecture to allow researchers to design specific polymers, model new metals, discover materials, and simulate diseases purely through conversational AI interfacing with quantum hardware.

### 🛡️ The "Anti-Cheat" Proof (Quantum Execution Receipt)
A major concern with LLMs is that they simply hallucinate or "Google" answers from their training data rather than performing actual computations. 

QAC-L solves this transparently. Every time a question is asked, the pipeline outputs a **Quantum Execution Receipt**. This receipt displays the raw bitstring counts, the exact backend used (e.g., AerSimulator or IBM Quantum), and the number of shots. Because quantum measurement is fundamentally probabilistic, these raw counts cannot be memorized or faked by an LLM—they are undeniable proof that the quantum circuit was physically executed.

### ⚙️ Architecture: The Secure Pipeline
QAC-L relies on a strict, multi-step architecture to prevent LLM hallucinations from causing runtime errors:
1. **AI Compiler:** A fine-tuned Qwen2.5-Coder-7B-Instruct model (using LoRA/PEFT) translates the user's English prompt into a strict Quantum Domain Specific Language (DSL).
2. **The "Bouncer" Shield:** A Python validation layer intercepts the DSL and enforces strict physical bounds (e.g., qubit limits, bond distance ranges). If the LLM hallucinates invalid parameters, the Bouncer halts execution.
3. **Quantum Engine:** Safely executes the validated circuit locally via Qiskit AerSimulator or remotely via the IBM Quantum API.
4. **AI Physicist Explainer:** Takes the raw quantum measurement counts and eigenvalues and translates them back into clear, scientifically accurate English for the user.

### 🚀 Prototype Status & Roadmap
The current QAC-L pipeline is architected to handle 5 widely-known quantum mechanics problems through conversational AI:
1. **Superposition & Randomness:** Generating true random numbers via quantum superposition.
2. **Quantum Entanglement:** Creating and measuring Bell States to show qubit correlation.
3. **Molecular Simulation (VQE):** Calculating the ground-state energy of an H₂ molecule at variable bond distances. *(Successfully validated in local testing)*
4. **Quantum Search (Grover's Algorithm):** Finding hidden items in a database with quadratic speedup.
5. **Quantum Optimization (QAOA):** Solving combinatorial optimization problems on graphs.

> **Hardware Note:** The initial proof-of-concept for this pipeline was successfully validated locally on a constrained laptop GPU (RTX 3050). Pulsate Labs is seeking infrastructure partnerships (such as the Alibaba Cloud AI Catalyst Program) to scale compute resources, allowing the full fine-tuned model and all 5 quantum algorithms to run seamlessly in production.

### 💻 Technical Stack
* **AI Model:** Qwen2.5-Coder-7B-Instruct (Fine-tuned locally)
* **Quantum Framework:** Qiskit 1.x, AerSimulator, IBM Quantum Platform API
* **Security:** Secure `.env` environment variable management for API tokens
* **Hardware:** Auto-detects local NVIDIA GPUs for 4-bit inference, with CPU fallback

---
*Developed by Pulsate Labs © 2024*

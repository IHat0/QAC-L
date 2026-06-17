#!/usr/bin/env python3
"""
quantum_ai_pipeline.py — Integrated AI-Quantum Closed-Loop Pipeline

Compiles English prompts to Quantum DSL via your fine-tuned Qwen adapter,
validates and executes them via Qiskit locally, and explains raw quantum data 
back to the user using physics-informed prompt context.
"""

import os
import re
import sys
import torch

# ═══════════════════════════════════════════════════════════════════════════════
# 1. LOAD LOCAL QUANTUM BOUNCER & HARDWARE DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════
from quantum_bouncer import (
    parse_and_validate_dsl, 
    run_random_circuit, 
    run_vqe_circuit, 
    _print_receipt,
    BACKEND_LABEL
)

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
ADAPTER_PATH = "./qwen-quantum-adapter"

print()
print("╔══════════════════════════════════════════════════════════════════╗")
print("║             Starting Local AI-Quantum Orchestrator               ║")
print("╚══════════════════════════════════════════════════════════════════╝")

# Validate local adapter folder exists
if not os.path.exists(ADAPTER_PATH) or not os.path.exists(os.path.join(ADAPTER_PATH, "adapter_model.safetensors")):
    print(f"[ERROR] Could not find unzipped adapter folder at {ADAPTER_PATH}.")
    print("Please ensure the unzipped files are placed directly inside C:\\qac-1\\qwen-quantum-adapter\\")
    sys.exit(1)

print("⟳ Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)

# Auto-detect local hardware capabilities
if torch.cuda.is_available():
    print("⟳ NVIDIA GPU detected! Loading base model in 4-bit precision...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        dtype=torch.bfloat16,
        trust_remote_code=True
    )
else:
    print("⟳ No CUDA GPU detected. Loading base model on local CPU (this may take a minute)...")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="cpu",
        low_cpu_mem_usage=True,
        trust_remote_code=True
    )

print("⟳ Applying fine-tuned Quantum Adapters...")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model.eval()
print("[SUCCESS] AI-Quantum local environment loaded and ready.")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. COMPILING AND EXPLAINING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def translate_to_dsl(english_prompt: str) -> str:
    """Translates conversational English into our strict custom quantum DSL."""
    system_prompt = "You are a compiler. Translate the user's natural language request into the strict DSL format."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": english_prompt}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=64,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)]
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()


def explain_results(action: str, raw_data: dict, original_question: str) -> str:
    """Uses physics-informed prompting to interpret raw counts for the researcher."""
    system_prompt = (
        "You are a Senior Quantum Physicist. Translate raw quantum measurement counts and computed eigenvalues "
        "into a clear, scientifically accurate explanation in simple English. Note: Minor probabilities (<5%) "
        "of incorrect states represent normal hardware decoherence/quantum noise, which is expected. "
        "Explain the physical meaning of the computed energy or bitstrings in the context of the user's original query."
    )
    context = f"User Query: \"{original_question}\"\nAction: {action}\nBackend: {BACKEND_LABEL}\nRaw Output: {raw_data}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)]
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

# ═══════════════════════════════════════════════════════════════════════════════
# 3. INTERACTIVE TERMINAL LOOP
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n  Complete Local Pipeline Initialized.")
    print("  Type any natural language command (e.g. 'Can you simulate H2 at 0.735 Angstroms?').")
    print("  Type 'exit' or 'quit' to close.\n")

    while True:
        try:
            user_query = input("User ▸ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_query or user_query.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            break

        # Step A: Compile conversational input into DSL
        print("  ⟳ AI Compiler: Parsing English to DSL...")
        dsl_command = translate_to_dsl(user_query)
        print(f"  └─> Compiled DSL: {dsl_command}")

        # Step B: Shield validation
        parsed = parse_and_validate_dsl(dsl_command)
        if "error" in parsed:
            print(f"  └─> [BLOCKED] Shield halted execution: {parsed['error']}\n")
            continue
        
        action = parsed["action"]
        print(f"  └─> [APPROVED] Executing {action} action on Qiskit...")

        # Step C: Execute Quantum Circuits
        try:
            if action == "RANDOM":
                quantum_data = run_random_circuit(parsed["qubits"])
            elif action == "VQE":
                print("  ⟳ Quantum Engine: Running parameter sweep...")
                quantum_data = run_vqe_circuit(parsed["distance"])
            
            # Print standard execution receipt
            _print_receipt(action, quantum_data)

            # Step D: Conversational Explanation
            print("  ⟳ AI Physicist: Translating raw counts into scientific English...")
            explanation = explain_results(action, quantum_data, user_query)
            print("🔬 [AI SCIENTIFIC INTERPRETATION]:")
            print(explanation)
            print("═" * 62 + "\n")

        except Exception as exc:
            print(f"  [ERROR] Runtime failure: {exc}\n")
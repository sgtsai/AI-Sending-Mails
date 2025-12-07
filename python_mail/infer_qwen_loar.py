import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_MODEL = "Qwen/Qwen3-0.6B"
ADAPTER_DIR = "./qwen-lora-json"

def build_prompt(instruction: str):
    # Keep the same format the model saw during fine-tuning
    return f"Instruction: {instruction}\nOutput: "

def generate_output(instruction: str, max_new_tokens=128):
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
    base = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    model = PeftModel.from_pretrained(base, ADAPTER_DIR)
    model.eval()

    prompt = build_prompt(instruction)
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,    # deterministic; set True for sampling
        temperature=0.0
    )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the generated part after "Output: "
    gen = text.split("Output: ", 1)[-1].strip()
    # Trim to first {...}
    start = gen.find("{")
    end = gen.find("}")
    if start != -1 and end != -1:
        gen_json = gen[start:end+1]
        try:
            return json.loads(gen_json)
        except Exception:
            return {"raw": gen_json, "error": "JSON parse failed"}
    return {"raw": gen, "error": "No JSON block found"}

if __name__ == "__main__":
    tests = [
        "Add caixintong with email f74146856@gs.ncku.edu.tw",
        "Send Bob an email saying meeting tomorrow at 10am",
        "Delete Alice from contacts",
        "Email Alice: can we reschedule to next Monday?"
    ]
    for t in tests:
        print("\nInstruction:", t)
        print("Output:", generate_output(t))

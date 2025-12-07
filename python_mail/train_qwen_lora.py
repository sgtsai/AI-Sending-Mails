import json
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model

BASE_MODEL = "Qwen/Qwen3-0.6B"
DATA_FILE = "dataset.jsonl"
OUTPUT_DIR = "./qwen-lora-json"

def format_example(instruction, output_obj):
    # Serialize output as compact JSON string
    return f"Instruction: {instruction}\nOutput: {json.dumps(output_obj, ensure_ascii=False)}"

def main():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)

    # Load dataset
    ds = load_dataset("json", data_files=DATA_FILE)["train"]

    # Map to text field
    ds = ds.map(lambda ex: {"text": format_example(ex["instruction"], ex["output"])}, remove_columns=ds.column_names)

    # Tokenize
    def tok_fn(ex):
        return tokenizer(ex["text"], truncation=True, max_length=512)
    ds_tokenized = ds.map(tok_fn, batched=True, remove_columns=ds.column_names)

    # LoRA config
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"]  # typical for Qwen
    )
    model = get_peft_model(model, lora_config)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=8,
        num_train_epochs=3,
        learning_rate=2e-4,
        logging_steps=20,
        save_steps=500,
        save_total_limit=2,
        fp16=True
        # Removed evaluation_strategy for compatibility
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_tokenized,
        data_collator=data_collator
    )

    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("✅ Training complete. Saved to", OUTPUT_DIR)

if __name__ == "__main__":
    main()

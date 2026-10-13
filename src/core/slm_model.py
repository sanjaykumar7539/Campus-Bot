from pathlib import Path
from config import config


class SLMModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_constructed', False):
            return
        self.model_path = config.MODEL_PATH
        self.model = self.tokenizer = self.pipe = None
        self._initialized = False
        self._constructed = True

    def files_present(self) -> bool:
        from .readiness import model_files_present
        return model_files_present(self.model_path)

    def load_model(self):
        if self._initialized:
            return
        if not self.files_present():
            raise FileNotFoundError(f'SLM model not found at {self.model_path}. Run scripts/download_model.py first.')
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path, torch_dtype=torch.bfloat16, device_map='auto',
            trust_remote_code=True, low_cpu_mem_usage=True,
        )
        self._initialized = True

    def generate(self, prompt: str, max_tokens: int = 384) -> str:
        if not self._initialized:
            self.load_model()
        import torch
        inputs = self.tokenizer(prompt, return_tensors='pt').to(self.model.device)
        with torch.inference_mode():
            output = self.model.generate(
                **inputs, max_new_tokens=max_tokens, temperature=0.1, top_p=0.9,
                repetition_penalty=1.1, do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        return self.tokenizer.decode(output[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True).strip()

    def format_prompt(self, system_prompt: str, context: str, query: str) -> str:
        return f'''<|system|>\n{system_prompt}\n\n<|user|>\nAnswer the question using ONLY the provided context.\n\nContext:\n{context}\n\nQuestion: {query}\n\n<|assistant|>\n'''

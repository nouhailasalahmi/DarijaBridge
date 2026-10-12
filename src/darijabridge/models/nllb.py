"""NLLB-200 translator (Hugging Face). The heavy imports are done lazily so that the rest of the
project (and the tests) work without torch/transformers installed."""
import time

from darijabridge.utils.logging import get_logger

log = get_logger("nllb")


class NllbTranslator:
    def __init__(self, model_name: str, src_lang: str, tgt_lang: str, num_beams: int = 4,
                 max_length: int = 128, batch_size: int = 16, device: str | None = None):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=src_lang)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device).eval()
        if self.device == "cuda":
            self.model.half()
        self.tgt_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
        if self.tgt_id == self.tokenizer.unk_token_id:
            raise ValueError(f"unknown target language code: {tgt_lang}")
        self.num_beams, self.max_length, self.batch_size = num_beams, max_length, batch_size
        log.info("model=%s device=%s src=%s tgt=%s", model_name, self.device, src_lang, tgt_lang)

    def translate(self, texts: list[str]) -> list[str]:
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))     # similar lengths per batch
        out = [""] * len(texts)
        start = time.time()
        for b in range(0, len(order), self.batch_size):
            ids = order[b:b + self.batch_size]
            batch = self.tokenizer([texts[i] for i in ids], return_tensors="pt", padding=True,
                                   truncation=True, max_length=self.max_length).to(self.device)
            with self.torch.no_grad():
                gen = self.model.generate(**batch, forced_bos_token_id=self.tgt_id,
                                          num_beams=self.num_beams, max_length=self.max_length)
            for i, text in zip(ids, self.tokenizer.batch_decode(gen, skip_special_tokens=True)):
                out[i] = text
            done = min(b + self.batch_size, len(order))
            log.info("%d/%d sentences (%.0f s)", done, len(order), time.time() - start)
        return out


class IdentityTranslator:
    """Copies the input. Used with --dry-run to check the whole pipeline without any model."""

    def translate(self, texts: list[str]) -> list[str]:
        return list(texts)

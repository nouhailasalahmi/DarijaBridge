"""A small, explicit training loop (mixed precision, gradient accumulation, linear schedule)."""
import json
import math
import time
from pathlib import Path

from darijabridge.training.data import collate, length_grouped_batches
from darijabridge.utils.logging import get_logger

log = get_logger("train")


def _make_optimizer(params, cfg):
    import torch

    name = cfg.get("optimizer", "adamw")
    if name == "adafactor":      # lighter in memory than AdamW: use it if the GPU runs out of memory
        return torch.optim.Adafactor(params, lr=cfg["learning_rate"], weight_decay=cfg.get("weight_decay", 0.0))
    return torch.optim.AdamW(params, lr=cfg["learning_rate"], weight_decay=cfg.get("weight_decay", 0.0))


def evaluate_loss(model, items, cfg, device, pad_id) -> float:
    """Mean token-level loss on `items` (no generation: fast)."""
    import torch

    model.eval()
    use_amp = cfg.get("fp16", False) and device == "cuda"
    total, count = 0.0, 0
    order = sorted(range(len(items)), key=lambda i: len(items[i][0]))
    bs = cfg["batch_size"] * 2
    with torch.no_grad():
        for b in range(0, len(order), bs):
            batch = {k: v.to(device) for k, v in collate([items[i] for i in order[b:b + bs]], pad_id).items()}
            with torch.autocast(device_type=device, dtype=torch.float16, enabled=use_amp):
                loss = model(**batch).loss
            n = int((batch["labels"] != -100).sum())
            total += float(loss) * n
            count += n
    model.train()
    return total / max(count, 1)


def train(model, tokenizer, train_items, val_items, cfg: dict, device: str, pad_id: int, out_dir: str | Path) -> dict:
    import torch

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(cfg.get("seed", 42))
    use_amp = cfg.get("fp16", False) and device == "cuda"
    accum = cfg.get("grad_accum_steps", 1)
    steps_per_epoch = math.ceil(math.ceil(len(train_items) / cfg["batch_size"]) / accum)
    total_steps = cfg["max_steps"] if cfg.get("max_steps") else cfg["epochs"] * steps_per_epoch
    warmup = max(1, int(cfg.get("warmup_ratio", 0.05) * total_steps))

    opt = _make_optimizer(model.parameters(), cfg)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min((s + 1) / warmup, max(0.0, (total_steps - s) / max(1, total_steps - warmup))))
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    lengths = [len(x) for x, _ in train_items]

    history, best, step, t0 = [], float("inf"), 0, time.time()
    log_file = (out_dir / "train_log.jsonl").open("w", encoding="utf-8")

    def record(**kw):
        kw["seconds"] = round(time.time() - t0)
        history.append(kw)
        log_file.write(json.dumps(kw) + "\n"); log_file.flush()
        log.info(" ".join(f"{k}={v}" for k, v in kw.items()))

    def validate():
        nonlocal best
        loss = evaluate_loss(model, val_items, cfg, device, pad_id)
        record(step=step, val_loss=round(loss, 4))
        if loss < best:
            best = loss
            model.save_pretrained(out_dir / "best"); tokenizer.save_pretrained(out_dir / "best")

    model.train()
    log.info("%d training pairs, %d steps (%d per epoch), device=%s, amp=%s",
             len(train_items), total_steps, steps_per_epoch, device, use_amp)
    running, seen = 0.0, 0
    done = False
    for epoch in range(cfg["epochs"]):
        for i, idx in enumerate(length_grouped_batches(lengths, cfg["batch_size"], cfg.get("seed", 42) + epoch)):
            batch = {k: v.to(device) for k, v in collate([train_items[j] for j in idx], pad_id).items()}
            with torch.autocast(device_type=device, dtype=torch.float16, enabled=use_amp):
                loss = model(**batch).loss / accum
            scaler.scale(loss).backward()
            running += float(loss.detach()) * accum
            seen += 1
            if (i + 1) % accum:
                continue
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.get("max_grad_norm", 1.0))
            scaler.step(opt); scaler.update(); sched.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if step % cfg.get("log_every", 50) == 0:
                record(step=step, epoch=epoch, train_loss=round(running / seen, 4), lr=round(sched.get_last_lr()[0], 8))
                running, seen = 0.0, 0
            if cfg.get("eval_every") and step % cfg["eval_every"] == 0:
                validate()
            if step >= total_steps:
                done = True
                break
        if done:
            break
    validate()
    model.save_pretrained(out_dir / "last"); tokenizer.save_pretrained(out_dir / "last")
    log_file.close()
    return {"steps": step, "best_val_loss": round(best, 4), "seconds": round(time.time() - t0), "history": history}
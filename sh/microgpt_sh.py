"""
Character-level micro GPT training with NumPy data prep and PyTorch execution.

The original version kept every scalar operation in pure Python for teaching.
This version keeps the same small GPT shape and dataset flow, but delegates
tensor math, autograd, and Adam updates to PyTorch.
"""

import os
import random
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


SEED = 42
N_LAYER = 1
N_EMBD = 16
BLOCK_SIZE = 16
N_HEAD = 4
NUM_STEPS = 1000
NUM_SAMPLES = 20
TEMPERATURE = 0.5
LEARNING_RATE = 0.01
BETA1 = 0.85
BETA2 = 0.99
EPS_ADAM = 1e-8

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_PATH = os.path.join(PROJECT_ROOT, "input.txt")


@dataclass(frozen=True)
class Tokenizer:
    uchars: np.ndarray
    stoi: dict[str, int]
    bos: int

    @property
    def vocab_size(self):
        return self.bos + 1


def seed_everything(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_docs(path=INPUT_PATH):
    if not os.path.exists(path):
        import urllib.request

        names_url = "https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt"
        urllib.request.urlretrieve(names_url, path)
    with open(path, encoding="utf-8") as f:
        docs = [line.strip() for line in f if line.strip()]
    random.shuffle(docs)
    return docs


def build_tokenizer(docs):
    uchars = np.array(sorted(set("".join(docs))))
    stoi = {ch: i for i, ch in enumerate(uchars.tolist())}
    return Tokenizer(uchars=uchars, stoi=stoi, bos=len(uchars))


def encode_doc(doc, tokenizer):
    ids = np.fromiter((tokenizer.stoi[ch] for ch in doc), dtype=np.int64)
    return np.concatenate(([tokenizer.bos], ids, [tokenizer.bos])).astype(np.int64)


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class RMSNorm(nn.Module):
    def forward(self, x):
        return x * torch.rsqrt((x * x).mean(dim=-1, keepdim=True) + 1e-5)


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        head_dim = N_EMBD // N_HEAD
        if head_dim * N_HEAD != N_EMBD:
            raise ValueError("N_EMBD must be divisible by N_HEAD")
        self.head_dim = head_dim
        self.attn_wq = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.attn_wk = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.attn_wv = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.attn_wo = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.mlp_fc1 = nn.Linear(N_EMBD, 4 * N_EMBD, bias=False)
        self.mlp_fc2 = nn.Linear(4 * N_EMBD, N_EMBD, bias=False)
        self.rmsnorm = RMSNorm()

    def forward(self, x):
        batch_size, seq_len, _ = x.shape

        x_residual = x
        x = self.rmsnorm(x)
        q = self.attn_wq(x)
        k = self.attn_wk(x)
        v = self.attn_wv(x)

        q = q.view(batch_size, seq_len, N_HEAD, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, N_HEAD, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, N_HEAD, self.head_dim).transpose(1, 2)

        attn_logits = q @ k.transpose(-2, -1) / (self.head_dim**0.5)
        causal_mask = torch.triu(
            torch.ones(seq_len, seq_len, dtype=torch.bool, device=x.device),
            diagonal=1,
        )
        attn_logits = attn_logits.masked_fill(causal_mask, float("-inf"))
        attn_weights = F.softmax(attn_logits, dim=-1)
        x_attn = attn_weights @ v
        x_attn = x_attn.transpose(1, 2).contiguous().view(batch_size, seq_len, N_EMBD)
        x = self.attn_wo(x_attn) + x_residual

        x_residual = x
        x = self.rmsnorm(x)
        x = self.mlp_fc1(x)
        x = F.relu(x)
        x = self.mlp_fc2(x)
        return x + x_residual


class TinyGPT(nn.Module):
    def __init__(self, vocab_size, block_size=BLOCK_SIZE):
        super().__init__()
        self.block_size = block_size
        self.wte = nn.Embedding(vocab_size, N_EMBD)
        self.wpe = nn.Embedding(block_size, N_EMBD)
        self.blocks = nn.ModuleList([Block() for _ in range(N_LAYER)])
        self.rmsnorm = RMSNorm()
        self.lm_head = nn.Linear(N_EMBD, vocab_size, bias=False)
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Embedding, nn.Linear)):
            nn.init.normal_(module.weight, mean=0.0, std=0.08)

    def forward(self, token_ids):
        batch_size, seq_len = token_ids.shape
        if seq_len > self.block_size:
            raise ValueError(f"sequence length {seq_len} exceeds block_size {self.block_size}")
        pos_ids = torch.arange(seq_len, device=token_ids.device).unsqueeze(0).expand(batch_size, seq_len)
        x = self.wte(token_ids) + self.wpe(pos_ids)
        x = self.rmsnorm(x)
        for block in self.blocks:
            x = block(x)
        return self.lm_head(x)


def train(model, docs, tokenizer, device, num_steps=NUM_STEPS):
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        betas=(BETA1, BETA2),
        eps=EPS_ADAM,
    )

    for step in range(num_steps):
        tokens = encode_doc(docs[step % len(docs)], tokenizer)
        n = min(BLOCK_SIZE, len(tokens) - 1)
        input_ids = torch.tensor(tokens[:n], dtype=torch.long, device=device).unsqueeze(0)
        targets = torch.tensor(tokens[1 : n + 1], dtype=torch.long, device=device).unsqueeze(0)

        logits = model(input_ids)
        loss = F.cross_entropy(logits.reshape(-1, tokenizer.vocab_size), targets.reshape(-1))

        optimizer.zero_grad(set_to_none=True)
        loss.backward()

        lr_t = LEARNING_RATE * (1 - step / num_steps)
        for group in optimizer.param_groups:
            group["lr"] = lr_t
        optimizer.step()

        print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.item():.4f}", end="\r")


@torch.no_grad()
def generate_samples(model, tokenizer, device, num_samples=NUM_SAMPLES, temperature=TEMPERATURE):
    model.eval()
    samples = []
    for _ in range(num_samples):
        token_ids = [tokenizer.bos]
        sample_chars = []
        for _pos_id in range(BLOCK_SIZE):
            input_ids = torch.tensor([token_ids[-BLOCK_SIZE:]], dtype=torch.long, device=device)
            logits = model(input_ids)[0, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            next_id = int(torch.multinomial(probs, num_samples=1).item())
            if next_id == tokenizer.bos:
                break
            sample_chars.append(str(tokenizer.uchars[next_id]))
            token_ids.append(next_id)
        samples.append("".join(sample_chars))
    model.train()
    return samples


def main():
    seed_everything()
    docs = load_docs()
    tokenizer = build_tokenizer(docs)
    device = get_device()
    model = TinyGPT(tokenizer.vocab_size).to(device)

    print(f"num docs: {len(docs)}")
    print(f"vocab size: {tokenizer.vocab_size}")
    print(f"num params: {sum(p.numel() for p in model.parameters())}")
    print(f"device: {device}")

    train(model, docs, tokenizer, device)

    print("\n--- inference (new, hallucinated names) ---")
    for sample_idx, sample in enumerate(generate_samples(model, tokenizer, device), start=1):
        print(f"sample {sample_idx:2d}: {sample}")


if __name__ == "__main__":
    main()

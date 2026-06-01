"""
PyTorch version of microgpt_for_mod.py.
Keeps the same modulo-addition task, model shape, training loop, and evaluation
flow, but delegates tensors and autograd to PyTorch.
"""

import os       # os.path.exists
import random   # random.seed, random.shuffle

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ModuleNotFoundError:
    raise ModuleNotFoundError("PyTorch is required to run this file. Install torch first.") from None

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(device)

random.seed(42) # Let there be order among chaos
torch.manual_seed(42)

# Modulo addition task setting
MODULUS = 23
INPUT_PATH = 'input.txt'
if MODULUS < 2:
    raise ValueError("MODULUS must be at least 2")

# Let there be a Dataset `docs`: list[str] of modulo addition examples, e.g. "4 + 14 = 18"
if not os.path.exists(INPUT_PATH):
    raise FileNotFoundError(f"expected {INPUT_PATH} with lines like '4 + 14 = 18'")
docs = [line.strip() for line in open(INPUT_PATH) if line.strip()]
random.shuffle(docs)
print(f"num docs: {len(docs)}")

def parse_example(doc):
    parts = doc.split()
    if len(parts) != 5 or parts[1] != '+' or parts[3] != '=':
        raise ValueError(f"bad example format: {doc!r}")
    a, b, target = int(parts[0]), int(parts[2]), int(parts[4])
    if not (0 <= a < MODULUS and 0 <= b < MODULUS and 0 <= target < MODULUS):
        raise ValueError(f"example out of range for MODULUS={MODULUS}: {doc!r}")
    expected = (a + b) % MODULUS
    if target != expected:
        raise ValueError(f"wrong target for MODULUS={MODULUS}: {doc!r}, expected {expected}")
    return a, b, target

examples = [parse_example(doc) for doc in docs]

# Let there be a Tokenizer to translate strings to sequences of integers ("tokens") and back
utokens = [str(i) for i in range(MODULUS)] # number tokens become token ids 0..n-1
stoi = {token: i for i, token in enumerate(utokens)}
itos = {i: token for token, i in stoi.items()}
vocab_size = len(utokens) # total number of unique tokens
print(f"vocab size: {vocab_size}")
print(utokens)

def encode_prompt(a, b):
    return [stoi[str(a)], stoi[str(b)]]

# Initialize the model hyperparameters
n_layer = 1     # depth of the transformer neural network (number of layers)
n_embd = 16     # width of the network (embedding dimension)
block_size = 2  # maximum context length of the attention window: a b
n_head = 4      # number of attention heads
head_dim = n_embd // n_head # derived dimension of each head

class RMSNorm(nn.Module):
    def forward(self, x):
        ms = (x * x).mean(dim=-1, keepdim=True)
        return x * torch.rsqrt(ms + 1e-5)

class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.attn_wq = nn.Linear(n_embd, n_embd, bias=False)
        self.attn_wk = nn.Linear(n_embd, n_embd, bias=False)
        self.attn_wv = nn.Linear(n_embd, n_embd, bias=False)
        self.attn_wo = nn.Linear(n_embd, n_embd, bias=False)
        self.mlp_fc1 = nn.Linear(n_embd, 4 * n_embd, bias=False)
        self.mlp_fc2 = nn.Linear(4 * n_embd, n_embd, bias=False)
        self.rmsnorm = RMSNorm()

    def forward(self, x):
        bsz, seq_len, _ = x.shape

        # 1) Multi-head Attention block
        x_residual = x
        x = self.rmsnorm(x)
        q = self.attn_wq(x)
        k = self.attn_wk(x)
        v = self.attn_wv(x)

        q = q.view(bsz, seq_len, n_head, head_dim).transpose(1, 2)
        k = k.view(bsz, seq_len, n_head, head_dim).transpose(1, 2)
        v = v.view(bsz, seq_len, n_head, head_dim).transpose(1, 2)

        attn_logits = q @ k.transpose(-2, -1) / (head_dim ** 0.5)
        causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device, dtype=torch.bool), diagonal=1)
        attn_logits = attn_logits.masked_fill(causal_mask, float('-inf'))
        attn_weights = F.softmax(attn_logits, dim=-1)
        x_attn = attn_weights @ v
        x_attn = x_attn.transpose(1, 2).contiguous().view(bsz, seq_len, n_embd)
        x = self.attn_wo(x_attn)
        x = x + x_residual

        # 2) MLP block
        x_residual = x
        x = self.rmsnorm(x)
        x = self.mlp_fc1(x)
        x = F.relu(x)
        x = self.mlp_fc2(x)
        x = x + x_residual
        return x

class TinyGPT(nn.Module):
    def __init__(self):
        super().__init__()
        self.wte = nn.Embedding(vocab_size, n_embd)
        self.wpe = nn.Embedding(block_size, n_embd)
        self.blocks = nn.ModuleList([Block() for _ in range(n_layer)])
        self.rmsnorm = RMSNorm()
        self.lm_head = nn.Linear(n_embd, vocab_size, bias=False)
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Embedding, nn.Linear)):
            nn.init.normal_(module.weight, mean=0.0, std=0.08)

    def forward(self, token_ids):
        bsz, seq_len = token_ids.shape
        if seq_len > block_size:
            raise ValueError(f"sequence length {seq_len} exceeds block_size {block_size}")
        pos_ids = torch.arange(seq_len, device=token_ids.device).unsqueeze(0).expand(bsz, seq_len)
        x = self.wte(token_ids) + self.wpe(pos_ids)
        x = self.rmsnorm(x)
        for block in self.blocks:
            x = block(x)
        logits = self.lm_head(x)
        return logits

device = torch.device(
    'cuda' if torch.cuda.is_available()
    else 'mps' if torch.backends.mps.is_available()
    else 'cpu'
)
model = TinyGPT().to(device)
params = list(model.parameters())
print(f"num params: {sum(p.numel() for p in params)}")
print(f"device: {device}")

# Let there be Adam, the blessed optimizer and its buffers
learning_rate, beta1, beta2, eps_adam = 0.01, 0.85, 0.99, 1e-8
optimizer = torch.optim.Adam(params, lr=learning_rate, betas=(beta1, beta2), eps=eps_adam)

# Repeat in sequence
num_steps = 1200 # number of training steps
log_every = 50
for step in range(num_steps):

    # Feed "a b" and train only the next-token prediction for the answer.
    a, b, target = examples[step % len(examples)]
    prompt_tokens = torch.tensor([encode_prompt(a, b)], dtype=torch.long, device=device)
    target_id = torch.tensor([stoi[str(target)]], dtype=torch.long, device=device)

    logits = model(prompt_tokens)
    loss = F.cross_entropy(logits[:, -1, :], target_id)

    # Backward the loss, calculating the gradients with respect to all model parameters
    optimizer.zero_grad(set_to_none=True)
    loss.backward()

    # Adam optimizer update: update the model parameters based on the corresponding gradients
    lr_t = learning_rate * (1 - step / num_steps) # linear learning rate decay
    for group in optimizer.param_groups:
        group['lr'] = lr_t
    optimizer.step()

    if (step + 1) % log_every == 0 or step == 0:
        print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.item():.4f}")

@torch.no_grad()
def predict(a, b):
    model.eval()
    prompt_tokens = torch.tensor([encode_prompt(a, b)], dtype=torch.long, device=device)
    logits = model(prompt_tokens)
    pred_id = int(torch.argmax(logits[0, -1, :]).item())
    return int(itos[pred_id])

# Inference: evaluate all modulo-addition cases
print("\n--- evaluation ---")
correct = 0
total = 0
for a in range(MODULUS):
    for b in range(MODULUS):
        pred = predict(a, b)
        target = (a + b) % MODULUS
        correct += pred == target
        total += 1

print(f"accuracy: {correct}/{total} = {correct / total:.3f}")
print("--- samples ---")
sample_pairs = [
    (0, 0),
    (1 % MODULUS, (MODULUS // 3) % MODULUS),
    (MODULUS // 4, (MODULUS // 2 + 3) % MODULUS),
    (MODULUS - 4, MODULUS - 5),
    (MODULUS - 1, MODULUS - 1),
]
for a, b in sample_pairs:
    print(f"{a} + {b} = {predict(a, b)} (target {(a + b) % MODULUS})")

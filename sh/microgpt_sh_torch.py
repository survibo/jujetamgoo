"""
PyTorch + DirectML version of sh_for_mod.py.
Intel Arc GPU accelerated modulo addition training.
"""

import os, math, random, pickle
import torch
import torch.nn as nn
import torch.nn.functional as F

random.seed(42)
torch.manual_seed(42)

docs = [line.strip() for line in open('input_sh.txt') if line.strip()]
random.shuffle(docs)
print(f"num docs: {len(docs)}")

MOD = 50
num_eval_samples = 20
train_answer_only = True
include_stop_loss = True
num_eval_points = 20
num_eval_steps = 50
num_steps = 20000

utokens = sorted(set(' '.join(docs).split()))
stoi = {token: token_id for token_id, token in enumerate(utokens)}
BOS = len(utokens)
vocab_size = len(utokens) + 1
itos = {i: t for t, i in stoi.items()}
itos[BOS] = '<BOS>'
print(f"vocab size: {vocab_size}")
print(utokens)

required_tokens = ['+', '='] + [str(i) for i in range(MOD)]
for token in required_tokens:
    if token not in stoi:
        raise ValueError(f"token {token!r} is missing from input_sh.txt")

device = torch.device('cpu')
# Try DirectML first, then CUDA, then MPS, fallback CPU
try:
    import torch_directml
    device = torch_directml.device()
    print(f"Using DirectML: {device}")
except ImportError:
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"Using CUDA: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = torch.device('mps')
        print("Using MPS")
    else:
        print("Using CPU (install torch-directml for Intel GPU acceleration)")

n_layer = 4
n_embd = 64
block_size = 16
n_head = 4
head_dim = n_embd // n_head

def xavier_init(shape, std=0.08):
    return torch.empty(shape, device=device).normal_(0, std)

class RMSNorm(nn.Module):
    def forward(self, x):
        return x * torch.rsqrt((x * x).mean(dim=-1, keepdim=True) + 1e-5)

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

    def _init_weights(self, m, std=0.08):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, 0, std)

    def forward(self, x):
        x_res = x
        x = self.rmsnorm(x)
        q = self.attn_wq(x)
        k = self.attn_wk(x)
        v = self.attn_wv(x)

        bsz, seq_len, _ = x.shape
        q = q.view(bsz, seq_len, n_head, head_dim).transpose(1, 2)
        k = k.view(bsz, seq_len, n_head, head_dim).transpose(1, 2)
        v = v.view(bsz, seq_len, n_head, head_dim).transpose(1, 2)

        attn = q @ k.transpose(-2, -1) / (head_dim ** 0.5)
        mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device, dtype=torch.bool), diagonal=1)
        attn = attn.masked_fill(mask, float('-inf'))
        attn = F.softmax(attn, dim=-1)
        x_attn = attn @ v
        x_attn = x_attn.transpose(1, 2).contiguous().view(bsz, seq_len, n_embd)
        x = self.attn_wo(x_attn)
        x = x + x_res

        x_res = x
        x = self.rmsnorm(x)
        x = self.mlp_fc1(x)
        x = F.relu(x)
        x = self.mlp_fc2(x)
        x = x + x_res
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
        pos_ids = torch.arange(seq_len, device=token_ids.device).unsqueeze(0)
        x = self.wte(token_ids) + self.wpe(pos_ids)
        x = self.rmsnorm(x)
        for block in self.blocks:
            x = block(x)
        logits = self.lm_head(x)
        return logits

model = TinyGPT().to(device)
params = list(model.parameters())
print(f"num params: {sum(p.numel() for p in params)}")

optimizer = torch.optim.Adam(params, lr=0.001, betas=(0.85, 0.99), eps=1e-8)

eval_interval = max(1, num_steps // num_eval_points)
for step in range(num_steps):
    doc = docs[step % len(docs)]
    doc_tokens = doc.split()
    if '=' not in doc_tokens:
        continue
    eq_idx = doc_tokens.index('=')
    tokens = [BOS] + [stoi[t] for t in doc_tokens] + [BOS]
    eq_pos = eq_idx + 1
    n = min(block_size, len(tokens) - 1)
    need_positions = eq_pos + (2 if include_stop_loss else 1)
    if need_positions > n:
        continue

    input_ids = torch.tensor(tokens[:n], dtype=torch.long, device=device).unsqueeze(0)
    logits = model(input_ids)

    target_positions = [eq_pos]
    if include_stop_loss:
        target_positions.append(eq_pos + 1)

    losses = []
    for pos_id in target_positions:
        if pos_id >= n:
            continue
        target_id = tokens[pos_id + 1]
        loss_t = F.cross_entropy(logits[0, pos_id:pos_id+1, :], torch.tensor([target_id], device=device))
        losses.append(loss_t)

    loss = torch.stack(losses).mean() if losses else torch.tensor(0.0, device=device)

    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()

    if step % eval_interval == 0 or step == num_steps - 1:
        model.eval()
        correct = 0
        with torch.no_grad():
            for _ in range(num_eval_steps):
                a = random.randrange(MOD)
                b = random.randrange(MOD)
                expected = str((a + b) % MOD)
                prompt = [BOS, stoi[str(a)], stoi['+'], stoi[str(b)], stoi['=']]
                inp = torch.tensor([prompt], dtype=torch.long, device=device)
                out = model(inp)
                pred_id = out[0, -1].argmax().item()
                predicted = itos.get(pred_id, '')
                if predicted == expected:
                    correct += 1
        acc = correct / num_eval_steps * 100
        model.train()
        print(f"\nstep {step+1:5d} / {num_steps:5d} | loss {loss.item():.4f} | eval_acc {acc:.1f}%")
    elif step % 100 == 0:
        print(f"step {step+1:5d} / {num_steps:5d} | loss {loss.item():.4f}", end='\r')

os.makedirs('checkpoints', exist_ok=True)
save_dict = {k: v.cpu().numpy() if isinstance(v, torch.Tensor) else v
             for k, v in model.state_dict().items()}
np_save = {}
for k, v in model.state_dict().items():
    np_save[k] = v.cpu().numpy()
np.savez('checkpoints/model_torch.npz', **np_save)
print(f"\n--- model saved to checkpoints/model_torch.npz ---")

print(f"\n--- inference (mod {MOD} addition) ---")
model.eval()
inference_records = []
for sample_idx in range(num_eval_samples):
    a = random.randrange(MOD)
    b = random.randrange(MOD)
    expected = str((a + b) % MOD)
    prompt = [BOS, stoi[str(a)], stoi['+'], stoi[str(b)], stoi['=']]

    with torch.no_grad():
        inp = torch.tensor([prompt], dtype=torch.long, device=device)
        out = model(inp)
        answer_tokens = []
        for pp in range(len(prompt), block_size):
            pred_id = out[0, -1].argmax().item()
            if pred_id == BOS:
                break
            answer_tokens.append(itos[pred_id])
            inp = torch.cat([inp, torch.tensor([[pred_id]], dtype=torch.long, device=device)], dim=1)
            out = model(inp)

    predicted = ' '.join(answer_tokens)
    status = 'OK' if predicted == expected else 'NO'
    print(f"sample {sample_idx+1:2d}: {a} + {b} = {predicted} | expected {expected} | {status}")

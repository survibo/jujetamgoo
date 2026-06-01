"""
The most atomic way to train and run inference for a GPT in pure Python + numpy.
This file is the complete algorithm.
Everything else is just efficiency.
@karpathy
"""

import os, math, random, pickle
import numpy as np
random.seed(42)
np.random.seed(42)

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
print(f"vocab size: {vocab_size}")
print(utokens)

required_tokens = ['+', '='] + [str(i) for i in range(MOD)]
for token in required_tokens:
    if token not in stoi:
        raise ValueError(f"token {token!r} is missing from input_sh.txt; regenerate data for MOD={MOD}")

class Param:
    __slots__ = ('data', 'grad')
    def __init__(self, data):
        self.data = data
        self.grad = np.zeros_like(data)

def matrix(nout, nin, std=0.08):
    return np.random.randn(nout, nin).astype(np.float64) * std

n_layer = 4
n_embd = 64
block_size = 16
n_head = 4
head_dim = n_embd // n_head

state_dict = {}
state_dict['wte'] = Param(matrix(vocab_size, n_embd))
state_dict['wpe'] = Param(matrix(block_size, n_embd))
state_dict['lm_head'] = Param(matrix(vocab_size, n_embd))
for i in range(n_layer):
    state_dict[f'layer{i}.attn_wq'] = Param(matrix(n_embd, n_embd))
    state_dict[f'layer{i}.attn_wk'] = Param(matrix(n_embd, n_embd))
    state_dict[f'layer{i}.attn_wv'] = Param(matrix(n_embd, n_embd))
    state_dict[f'layer{i}.attn_wo'] = Param(matrix(n_embd, n_embd))
    state_dict[f'layer{i}.mlp_fc1'] = Param(matrix(4 * n_embd, n_embd))
    state_dict[f'layer{i}.mlp_fc2'] = Param(matrix(n_embd, 4 * n_embd))
params = list(state_dict.values())
total_params = sum(p.data.size for p in params)
print(f"num params: {total_params}")

def rmsnorm(x):
    return x / np.sqrt(np.mean(x ** 2) + 1e-5)

def rmsnorm_backward(x, dy):
    n = x.shape[0]
    ms = np.mean(x ** 2) + 1e-5
    s = np.sqrt(ms)
    return dy / s - x * np.sum(dy * x) / (n * ms * s)

def softmax(x):
    x = x - np.max(x)
    e = np.exp(x)
    return e / np.sum(e)

def gpt_forward(token_id, pos_id, keys_k, keys_v):
    tok_emb = state_dict['wte'].data[token_id]
    pos_emb = state_dict['wpe'].data[pos_id]
    x = tok_emb + pos_emb
    cache = {'embed': x.copy(), 'token_id': token_id, 'pos_id': pos_id, 'layers': []}
    x = rmsnorm(x)
    cache['rms0'] = x.copy()

    for li in range(n_layer):
        lc = {}
        lc['x_in'] = x.copy()
        x_res = x.copy()
        x = rmsnorm(x)
        lc['rms1_in'] = x_res.copy()
        lc['rms1'] = x.copy()

        wq = state_dict[f'layer{li}.attn_wq'].data
        wk = state_dict[f'layer{li}.attn_wk'].data
        wv = state_dict[f'layer{li}.attn_wv'].data

        q = wq @ x
        k = wk @ x
        v = wv @ x
        lc['q'] = q.copy()
        lc['k'] = k.copy()
        lc['v'] = v.copy()
        keys_k[li].append(k)
        keys_v[li].append(v)

        head_outs = []
        attn_caches = []
        for h in range(n_head):
            hs = h * head_dim
            q_h = q[hs:hs+head_dim]
            k_list = [k_arr[hs:hs+head_dim] for k_arr in keys_k[li]]
            v_list = [v_arr[hs:hs+head_dim] for v_arr in keys_v[li]]
            scores = np.array([np.dot(q_h, k_i) / math.sqrt(head_dim) for k_i in k_list])
            x_safe = scores - np.max(scores)
            e = np.exp(x_safe)
            weights = e / np.sum(e)
            out_h = sum(w * v_i for w, v_i in zip(weights, v_list))
            head_outs.append(out_h)
            attn_caches.append({
                'scores': scores, 'weights': weights,
                'q_h': q_h.copy(),
                'k_list': [k.copy() for k in k_list],
                'v_list': [v.copy() for v in v_list],
            })

        attn_concat = np.concatenate(head_outs)
        lc['attn_concat'] = attn_concat.copy()
        lc['attn_caches'] = attn_caches

        wo = state_dict[f'layer{li}.attn_wo'].data
        x_attn = wo @ attn_concat
        x = x_attn + x_res
        lc['mid'] = x.copy()

        x_rms2 = x.copy()
        x = rmsnorm(x)
        lc['rms2_in'] = x_rms2.copy()
        lc['rms2'] = x.copy()

        fc1 = state_dict[f'layer{li}.mlp_fc1'].data
        x_fc1 = fc1 @ x
        lc['fc1'] = x_fc1.copy()
        x_relu = np.maximum(0, x_fc1)
        lc['relu'] = x_relu.copy()

        fc2 = state_dict[f'layer{li}.mlp_fc2'].data
        x_fc2 = fc2 @ x_relu
        lc['fc2'] = x_fc2.copy()

        x = x_fc2 + x_rms2
        lc['x_out'] = x.copy()
        cache['layers'].append(lc)

    logits = state_dict['lm_head'].data @ x
    cache['logits'] = logits.copy()
    cache['x_final'] = x.copy()
    return logits, cache

class Adam:
    def __init__(self, params, lr=0.01, beta1=0.85, beta2=0.99, eps=1e-8):
        self.params = params
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = [np.zeros_like(p.data) for p in params]
        self.v = [np.zeros_like(p.data) for p in params]

    def step(self, num_steps, step_idx):
        lr_t = self.lr * (1 - step_idx / num_steps)
        for i, p in enumerate(self.params):
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * p.grad
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * p.grad ** 2
            m_hat = self.m[i] / (1 - self.beta1 ** (step_idx + 1))
            v_hat = self.v[i] / (1 - self.beta2 ** (step_idx + 1))
            p.data -= lr_t * m_hat / (np.sqrt(v_hat) + self.eps)
            p.grad.fill(0.0)

optim = Adam(params, lr=0.001, beta1=0.85, beta2=0.99)

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

    keys_k = [[] for _ in range(n_layer)]
    keys_v = [[] for _ in range(n_layer)]
    caches = []
    for pos_id in range(n):
        logits, cache = gpt_forward(tokens[pos_id], pos_id, keys_k, keys_v)
        caches.append(cache)

    d_k = [[np.zeros(n_embd) for _ in range(block_size)] for _ in range(n_layer)]
    d_v = [[np.zeros(n_embd) for _ in range(block_size)] for _ in range(n_layer)]
    grad_above = [np.zeros(n_embd) for _ in range(n)]

    step_losses = []
    target_positions = [eq_pos]
    if include_stop_loss:
        target_positions.append(eq_pos + 1)

    for pos_id in target_positions:
        if pos_id >= n:
            continue
        target_id = tokens[pos_id + 1]
        logits = caches[pos_id]['logits']
        probs = softmax(logits)
        loss_t = -math.log(max(probs[target_id], 1e-15))
        step_losses.append(loss_t)
        d_logits = probs.copy()
        d_logits[target_id] -= 1.0
        grad_above[pos_id] = state_dict['lm_head'].data.T @ d_logits
        state_dict['lm_head'].grad += np.outer(d_logits, caches[pos_id]['x_final'])

    loss = sum(step_losses) / len(step_losses) if step_losses else 0.0

    # ── Backward: layers top→bottom, positions right→left ──
    for li in range(n_layer - 1, -1, -1):
        # k/v contributions to layer INPUT (rms1_in → previous layer output)
        grad_layer_in = [np.zeros(n_embd) for _ in range(n)]

        for pos_id in range(n - 1, -1, -1):
            dx_above = grad_above[pos_id]

            # Read & clear accumulated k/v gradient for this position at this layer
            dk_here = d_k[li][pos_id].copy() if np.any(d_k[li][pos_id]) else None
            dv_here = d_v[li][pos_id].copy() if np.any(d_v[li][pos_id]) else None
            d_k[li][pos_id].fill(0.0)
            d_v[li][pos_id].fill(0.0)

            has_grad = np.any(dx_above != 0) or dk_here is not None or dv_here is not None
            if not has_grad:
                continue

            lc = caches[pos_id]['layers'][li]
            n_kv = pos_id + 1

            dx = dx_above.copy()
            dx_fc2 = dx.copy()
            dx_mid = dx.copy()

            # FC2 backward
            state_dict[f'layer{li}.mlp_fc2'].grad += np.outer(dx_fc2, lc['relu'])
            d_relu = state_dict[f'layer{li}.mlp_fc2'].data.T @ dx_fc2

            d_fc1 = d_relu * (lc['fc1'] > 0).astype(np.float64)
            state_dict[f'layer{li}.mlp_fc1'].grad += np.outer(d_fc1, lc['rms2'])
            d_rms2_in = state_dict[f'layer{li}.mlp_fc1'].data.T @ d_fc1

            dx_mid += rmsnorm_backward(lc['rms2_in'], d_rms2_in)

            dx_attn = dx_mid.copy()
            dx_from_res = dx_mid.copy()

            state_dict[f'layer{li}.attn_wo'].grad += np.outer(dx_attn, lc['attn_concat'])
            d_attn_concat = state_dict[f'layer{li}.attn_wo'].data.T @ dx_attn

            # Multi-head attention backward
            d_q_all = np.zeros(n_embd)
            for h in range(n_head):
                hs = h * head_dim
                ac = lc['attn_caches'][h]
                d_head = d_attn_concat[hs:hs+head_dim]
                weights = ac['weights']
                d_weights = np.array([np.dot(d_head, ac['v_list'][t]) for t in range(n_kv)])
                d_scores = weights * (d_weights - np.sum(weights * d_weights))

                d_q_all[hs:hs+head_dim] = np.sum(
                    [d_scores[t] * ac['k_list'][t] for t in range(n_kv)], axis=0
                ) / math.sqrt(head_dim)

                for t in range(n_kv):
                    d_k[li][t][hs:hs+head_dim] += d_scores[t] * ac['q_h'] / math.sqrt(head_dim)
                    d_v[li][t][hs:hs+head_dim] += d_head * weights[t]

            # QKV backward: combine d_q, d_k[pos_id], d_v[pos_id]
            wq = state_dict[f'layer{li}.attn_wq']
            wk = state_dict[f'layer{li}.attn_wk']
            wv = state_dict[f'layer{li}.attn_wv']
            d_rms1 = np.zeros(n_embd)

            wq.grad += np.outer(d_q_all, lc['rms1'])
            d_rms1 += wq.data.T @ d_q_all

            if dk_here is not None:
                wk.grad += np.outer(dk_here, lc['rms1'])
                d_rms1 += wk.data.T @ dk_here
            if dv_here is not None:
                wv.grad += np.outer(dv_here, lc['rms1'])
                d_rms1 += wv.data.T @ dv_here

            # Own-attention k/v contribution (just added to d_k[li][pos_id])
            if np.any(d_k[li][pos_id]):
                wk.grad += np.outer(d_k[li][pos_id], lc['rms1'])
                d_rms1 += wk.data.T @ d_k[li][pos_id]
                d_k[li][pos_id].fill(0.0)
            if np.any(d_v[li][pos_id]):
                wv.grad += np.outer(d_v[li][pos_id], lc['rms1'])
                d_rms1 += wv.data.T @ d_v[li][pos_id]
                d_v[li][pos_id].fill(0.0)

            # RMSNorm backward + residual
            d_layer_in = rmsnorm_backward(lc['rms1_in'], d_rms1) + dx_from_res
            grad_above[pos_id] = d_layer_in

        # After all positions at this layer: propagate remaining d_k/d_v to lower layer
        for t in range(n - 1, -1, -1):
            if not np.any(d_k[li][t]) and not np.any(d_v[li][t]):
                continue
            ct = caches[t]['layers'][li]
            wk = state_dict[f'layer{li}.attn_wk']
            wv = state_dict[f'layer{li}.attn_wv']
            d_rms1 = np.zeros(n_embd)
            if np.any(d_k[li][t]):
                wk.grad += np.outer(d_k[li][t], ct['rms1'])
                d_rms1 += wk.data.T @ d_k[li][t]
                d_k[li][t].fill(0.0)
            if np.any(d_v[li][t]):
                wv.grad += np.outer(d_v[li][t], ct['rms1'])
                d_rms1 += wv.data.T @ d_v[li][t]
                d_v[li][t].fill(0.0)
            grad_layer_in[t] += rmsnorm_backward(ct['rms1_in'], d_rms1)

        # Merge k/v contributions into grad_above
        for t in range(n):
            if np.any(grad_layer_in[t]):
                grad_above[t] += grad_layer_in[t]

    # ── Embedding backward ──
    for pos_id in range(n):
        dx = grad_above[pos_id]
        if np.all(dx == 0):
            continue
        dx = rmsnorm_backward(caches[pos_id]['embed'], dx)
        state_dict['wte'].grad[tokens[pos_id]] += dx
        state_dict['wpe'].grad[pos_id] += dx

    optim.step(num_steps, step)

    if step % eval_interval == 0 or step == num_steps - 1:
        correct = 0
        for _ in range(num_eval_steps):
            a = random.randrange(MOD)
            b = random.randrange(MOD)
            expected = str((a + b) % MOD)
            prompt_tokens = [BOS, stoi[str(a)], stoi['+'], stoi[str(b)], stoi['=']]
            kk = [[] for _ in range(n_layer)]
            kv = [[] for _ in range(n_layer)]
            logits_out = None
            for pp, tt in enumerate(prompt_tokens):
                logits_out, _ = gpt_forward(tt, pp, kk, kv)
            pred = max(range(vocab_size), key=lambda i: logits_out[i])
            predicted = utokens[pred] if pred < len(utokens) else ''
            if predicted == expected:
                correct += 1
        acc = correct / num_eval_steps * 100
        print(f"\nstep {step+1:5d} / {num_steps:5d} | loss {loss:.4f} | eval_acc {acc:.1f}%")
    elif step % 100 == 0:
        print(f"step {step+1:5d} / {num_steps:5d} | loss {loss:.4f}", end='\r')

# ── Save model weights ──
os.makedirs('checkpoints', exist_ok=True)
save_dict = {k: p.data.copy() for k, p in state_dict.items()}
np.savez('checkpoints/model.npz', **save_dict)
print(f"\n--- model saved to checkpoints/model.npz ({os.path.getsize('checkpoints/model.npz')} bytes) ---")

# ── Detailed inference with activations ──
print(f"\n--- inference (mod {MOD} addition) ---")
inference_records = []
for sample_idx in range(num_eval_samples):
    a = random.randrange(MOD)
    b = random.randrange(MOD)
    expected = str((a + b) % MOD)
    prompt_tokens = [BOS, stoi[str(a)], stoi['+'], stoi[str(b)], stoi['=']]
    kk = [[] for _ in range(n_layer)]
    kv = [[] for _ in range(n_layer)]
    full_caches = []
    logits_out = None
    for pp, tt in enumerate(prompt_tokens):
        logits_out, cache = gpt_forward(tt, pp, kk, kv)
        full_caches.append(cache)
    answer_tokens = []
    for pp in range(len(prompt_tokens), block_size):
        token_id = max(range(vocab_size), key=lambda i: logits_out[i])
        if token_id == BOS:
            break
        answer_tokens.append(utokens[token_id])
        logits_out, cache = gpt_forward(token_id, pp, kk, kv)
        full_caches.append(cache)
    predicted = ' '.join(answer_tokens)
    status = 'OK' if predicted == expected else 'NO'
    print(f"sample {sample_idx+1:2d}: {a} + {b} = {predicted} | expected {expected} | {status}")

    # Collect activations for analysis
    logit_probs = softmax(logits_out) if logits_out is not None else None
    record = {
        'a': a, 'b': b, 'expected': expected, 'predicted': predicted, 'status': status,
        'n_positions': len(full_caches),
        'final_logits': logits_out.copy() if logits_out is not None else None,
        'final_probs': logit_probs.copy() if logit_probs is not None else None,
    }
    for pi, cache in enumerate(full_caches):
        record[f'pos{pi}_token_id'] = cache['token_id']
        record[f'pos{pi}_embed'] = cache['embed'].copy()
        record[f'pos{pi}_rms0'] = cache['rms0'].copy()
        for li in range(n_layer):
            lc = cache['layers'][li]
            record[f'pos{pi}_l{li}_x_in'] = lc['x_in'].copy()
            record[f'pos{pi}_l{li}_rms1'] = lc['rms1'].copy()
            record[f'pos{pi}_l{li}_q'] = lc['q'].copy()
            record[f'pos{pi}_l{li}_k'] = lc['k'].copy()
            record[f'pos{pi}_l{li}_v'] = lc['v'].copy()
            record[f'pos{pi}_l{li}_attn_concat'] = lc['attn_concat'].copy()
            record[f'pos{pi}_l{li}_mid'] = lc['mid'].copy()
            record[f'pos{pi}_l{li}_rms2'] = lc['rms2'].copy()
            record[f'pos{pi}_l{li}_fc1'] = lc['fc1'].copy()
            record[f'pos{pi}_l{li}_relu'] = lc['relu'].copy()
            record[f'pos{pi}_l{li}_fc2'] = lc['fc2'].copy()
            record[f'pos{pi}_l{li}_x_out'] = lc['x_out'].copy()
            for h in range(n_head):
                ac = lc['attn_caches'][h]
                record[f'pos{pi}_l{li}_h{h}_scores'] = ac['scores'].copy()
                record[f'pos{pi}_l{li}_h{h}_weights'] = ac['weights'].copy()
    inference_records.append(record)

with open('checkpoints/inference_records.pkl', 'wb') as f:
    pickle.dump(inference_records, f)
print(f"--- inference records saved to checkpoints/inference_records.pkl ---")

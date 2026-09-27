# Phase 24A — Failure Classification

Failure Classes:
- `F1` = insufficient reference support
- `F2` = no coarse structural recovery
- `F3` = coarse structure exists but LoFTR correspondence insufficient
- `F4` = LoFTR geometry initially passes but hold-out fails
- `F5` = validated relative-registration candidate exists

## Per-Pair Classification

### OHRC_PAIR_01
- **Result Class:** `F2`
- **Rationale:** No coarse structural recovery recovered from any predeclared offset.
- Coarse candidates: 49
  - SCREEN_PASS: 0
  - SCREEN_FAIL: 45
  - INSUFFICIENT_SUPPORT (F1 proxy): 4
- LoFTR verified: 0
- Initial QG pass: 0
- Full QG pass: 0
- F5 validated: 0

### OHRC_PAIR_02
- **Result Class:** `F3`
- **Rationale:** SCREEN_PASS candidates exist but LoFTR correspondence/geometry insufficient.
- Coarse candidates: 49
  - SCREEN_PASS: 13
  - SCREEN_FAIL: 36
  - INSUFFICIENT_SUPPORT (F1 proxy): 0
- LoFTR verified: 13
- Initial QG pass: 0
- Full QG pass: 0
- F5 validated: 0

### OHRC_PAIR_03
- **Result Class:** `F3`
- **Rationale:** SCREEN_PASS candidates exist but LoFTR correspondence/geometry insufficient.
- Coarse candidates: 49
  - SCREEN_PASS: 3
  - SCREEN_FAIL: 45
  - INSUFFICIENT_SUPPORT (F1 proxy): 1
- LoFTR verified: 3
- Initial QG pass: 0
- Full QG pass: 0
- F5 validated: 0

### OHRC_PAIR_04
- **Result Class:** `F2`
- **Rationale:** No coarse structural recovery recovered from any predeclared offset.
- Coarse candidates: 49
  - SCREEN_PASS: 0
  - SCREEN_FAIL: 45
  - INSUFFICIENT_SUPPORT (F1 proxy): 4
- LoFTR verified: 0
- Initial QG pass: 0
- Full QG pass: 0
- F5 validated: 0

## Per-Candidate Failure Drill-Down

### All SCREEN_PASS → LoFTR Results

| Key | dx_m | dy_m | n_cand | n_inl | ratio | occ | final_inl | held-out | gate | f-class |
|:---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|:---|
| OHRC_PAIR_02__dx-3000m_dy-3000m | -3000 | -3000 | 241 | 5 | 0.02075 | 0.3333 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx-3000m_dy-1000m | -3000 | -1000 | 234 | 5 | 0.02137 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx-3000m_dy+3000m | -3000 | 3000 | 192 | 6 | 0.03125 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx-2000m_dy+1000m | -2000 | 1000 | 247 | 6 | 0.02429 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx-1000m_dy-1000m | -1000 | -1000 | 248 | 6 | 0.02419 | 0.5556 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+0m_dy-2000m | 0 | -2000 | 210 | 6 | 0.02857 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+0m_dy+1000m | 0 | 1000 | 240 | 6 | 0.025 | 0.2222 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+1000m_dy-1000m | 1000 | -1000 | 240 | 6 | 0.025 | 0.3333 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+1000m_dy+3000m | 1000 | 3000 | 261 | 6 | 0.02299 | 0.3333 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+2000m_dy-2000m | 2000 | -2000 | 253 | 6 | 0.02372 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+2000m_dy-1000m | 2000 | -1000 | 258 | 7 | 0.02713 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+3000m_dy+2000m | 3000 | 2000 | 232 | 6 | 0.02586 | 0.3333 | 0 | False | False | F3 |
| OHRC_PAIR_02__dx+3000m_dy+3000m | 3000 | 3000 | 272 | 6 | 0.02206 | 0.3333 | 0 | False | False | F3 |
| OHRC_PAIR_03__dx-3000m_dy-2000m | -3000 | -2000 | 196 | 5 | 0.02551 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_03__dx-3000m_dy+2000m | -3000 | 2000 | 217 | 5 | 0.02304 | 0.4444 | 0 | False | False | F3 |
| OHRC_PAIR_03__dx+1000m_dy+2000m | 1000 | 2000 | 179 | 6 | 0.03352 | 0.3333 | 0 | False | False | F3 |

# external/

Third-party code cloned for reference/integration, not vendored into this
repo's git history (see `paper1_sarcrp/.gitignore`).

## CRP_RL

```
git clone --depth 1 https://github.com/operagang/CRP_RL.git
```

Shin, Choi, Cho, Kim (2026), *Learning to Retrieve Containers: A
Scale-diverse Deep Reinforcement Learning Approach for the Container
Retrieval Problem*, Transportation Research Part C. MIT license (code),
CC BY 4.0 (data). Pretrained checkpoints at
`CRP_RL/baselines/models/{proposed,online}/epoch(100).pt`.

`sarcrp.crp_rl_adapter` imports from this cloned copy at runtime (adds it
to `sys.path`). Clone it here before running anything that uses
`solve_crp_via_crp_rl`.

# Model resources

AILF uses a Qwen3-4B base model with a LoRA adapter and BGE retrieval over business candidates. Model loading occurs in the independent `celery_worker` service.

This directory contains training scripts, structured training examples, tokenizer / model configuration and adapter configuration. **Binary weights are not distributed in Git.** The checkpoint directories cannot be used for inference until compatible adapter weights have been placed there.

| Resource | Purpose |
| --- | --- |
| `train_pure_llm_v11.py` | Two-round task training with LoRA; review GPU, data and output settings before running |
| `inference_v11.py` | Local evaluation helpers; base and adapter paths can be supplied through environment variables |
| `dataset_v11*.jsonl` | Included structured training examples and train / validation files |
| `script/` | Dataset preparation utilities |
| `scene/` | Scenario definitions used by data utilities |
| `checkpoint_epoch_1/`, `checkpoint_epoch_2/` | Adapter configuration and tokenizer files; weights excluded |
| `bge-small-zh-v1.5/` | BGE configuration / tokenizer resources; weights excluded |

Use a separate GPU environment for training. Install a PyTorch build matching the hardware, then review `requirements.txt`. For serving dependencies, see [celery_worker/requirements.txt](../celery_worker/requirements.txt). Qwen3 requires a compatible Transformers version; older generic Transformers requirements are insufficient.

Code and resources must be evaluated under their respective licenses. The application's MIT license does not replace upstream model licenses. No measured accuracy or generalization claim is made by the presence of training scripts or checkpoint configuration.

Deployment paths and required files are documented in [deployment](../docs/DEPLOYMENT.md).

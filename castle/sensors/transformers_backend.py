"""PyTorch/Transformers implementation for the allowlisted sensor catalog."""

from __future__ import annotations

from functools import lru_cache

from .registry import SensorError, TEMPLATES


@lru_cache(maxsize=8)
def _load(model_id: str, revision: str, task: str, local_only: bool):
    import torch
    from transformers import AutoModel, AutoModelForMaskedLM
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    common = {
        "revision": revision,
        "local_files_only": local_only,
        "trust_remote_code": False,
    }
    tokenizer = AutoTokenizer.from_pretrained(model_id, **common)
    model_class = {
        "fill_mask": AutoModelForMaskedLM,
        "compare_text": AutoModel,
        "classify_labels": AutoModelForSequenceClassification,
    }[task]
    model = model_class.from_pretrained(model_id, use_safetensors=True, **common)
    model.eval()
    model.to(torch.device("cpu"))
    return tokenizer, model


class TransformersBackend:
    def __init__(self, *, allow_download: bool = False):
        self.local_only = not allow_download

    def _components(self, spec: dict):
        try:
            return _load(
                spec["model_id"], spec["revision"], spec["operation"], self.local_only
            )
        except OSError as exc:
            if self.local_only:
                raise SensorError(
                    "pinned checkpoint is not cached; rerun once with --allow-download"
                ) from exc
            raise

    def runtime_metadata(self) -> dict:
        import platform
        import torch
        import transformers

        return {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "device": "cpu",
            "remote_code": False,
            "safetensors_required": True,
        }

    def run(self, sensor: str, spec: dict, args: dict) -> dict:
        if spec["operation"] == "fill_mask":
            return self._fill_mask(spec, args)
        if spec["operation"] == "compare_text":
            return self._compare(spec, args)
        if spec["operation"] == "classify_labels":
            return self._classify(spec, args)
        raise SensorError(f"unsupported operation for {sensor}")

    def _fill_mask(self, spec: dict, args: dict) -> dict:
        import torch

        tokenizer, model = self._components(spec)
        encoded = tokenizer(
            args["text"], return_tensors="pt", truncation=True, max_length=spec["max_tokens"]
        )
        positions = (encoded["input_ids"] == tokenizer.mask_token_id).nonzero(as_tuple=False)
        if positions.shape[0] != 1:
            raise SensorError("[MASK] was missing after tokenization/truncation")
        with torch.inference_mode():
            logits = model(**encoded).logits[0, positions[0, 1]]
            probabilities = torch.softmax(logits, dim=-1)
            scores, token_ids = torch.topk(probabilities, args["top_k"])
        candidates = []
        for score, token_id in zip(scores.tolist(), token_ids.tolist()):
            replaced = encoded["input_ids"][0].clone()
            replaced[positions[0, 1]] = token_id
            candidates.append({
                "token": tokenizer.decode([token_id]).strip(),
                "score": round(float(score), 8),
                "sequence": tokenizer.decode(replaced, skip_special_tokens=True),
            })
        return {"candidates": candidates}

    def _compare(self, spec: dict, args: dict) -> dict:
        import torch
        import torch.nn.functional as functional

        tokenizer, model = self._components(spec)
        encoded = tokenizer(
            [args["left"], args["right"]], padding=True, truncation=True,
            max_length=spec["max_tokens"], return_tensors="pt"
        )
        with torch.inference_mode():
            token_embeddings = model(**encoded)[0]
            mask = encoded["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
            pooled = torch.sum(token_embeddings * mask, dim=1) / torch.clamp(
                mask.sum(dim=1), min=1e-9
            )
            normalized = functional.normalize(pooled, p=2, dim=1)
            cosine = torch.sum(normalized[0] * normalized[1]).item()
        return {
            "cosine_similarity": round(float(cosine), 8),
            "embedding_dimensions": int(normalized.shape[1]),
        }

    def _classify(self, spec: dict, args: dict) -> dict:
        import torch

        tokenizer, model = self._components(spec)
        hypotheses = [TEMPLATES[args["template"]].format(label) for label in args["labels"]]
        encoded = tokenizer(
            [args["text"]] * len(hypotheses), hypotheses, padding=True, truncation=True,
            max_length=spec["max_tokens"], return_tensors="pt"
        )
        with torch.inference_mode():
            logits = model(**encoded).logits
            per_pair = torch.softmax(logits, dim=1)
            entailment_index = spec["label_order"].index("entailment")
            entailment_logits = logits[:, entailment_index]
            relative = torch.softmax(entailment_logits, dim=0)
        ranked = [
            {
                "label": label,
                "relative_score": round(float(relative[index]), 8),
                "entailment_probability": round(float(per_pair[index, entailment_index]), 8),
            }
            for index, label in enumerate(args["labels"])
        ]
        ranked.sort(key=lambda item: item["relative_score"], reverse=True)
        return {
            "template": args["template"],
            "hypothesis_pattern": TEMPLATES[args["template"]],
            "ranking": ranked,
        }

"""LLM 调用封装：OpenAI 兼容接口 + 重试 + 并发 + 磁盘缓存 + 原始响应留档。

设计要点（针对原仓库缺陷）：
1. API key 只从环境变量 DEEPSEEK_API_KEY 读取，绝不写进文件；
2. 不使用任何本地代理（原仓库硬编码 127.0.0.1:7890），这里 trust_env=False；
3. 每次请求的 prompt / 原始响应 / usage / 耗时 / 重试次数 全部写入 JSONL；
4. 以 messages 的哈希做磁盘缓存，重复运行不重复计费；
5. 失败请求单独计数，不静默丢弃。
"""

import hashlib
import json
import os
import random
import threading
import time

import httpx
from openai import OpenAI


class LLMClient:
    def __init__(self, cfg, cache_dir, raw_log_path):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError(
                "未找到环境变量 DEEPSEEK_API_KEY。请先设置："
                "$env:DEEPSEEK_API_KEY='<your key>'"
            )
        self.model = cfg["model"]
        self.temperature = float(cfg.get("temperature", 0.0))
        self.top_p = float(cfg.get("top_p", 0.7))
        self.max_tokens = int(cfg.get("max_tokens", 8192))
        self.reasoning_effort = cfg.get("reasoning_effort") or None
        self.max_retries = int(cfg.get("max_retries", 5))
        self.retry_base_sleep = float(cfg.get("retry_base_sleep", 2))
        self.price_in = float(cfg.get("price_input_per_m", 1.0))
        self.price_out = float(cfg.get("price_output_per_m", 2.0))

        self.client = OpenAI(
            api_key=api_key,
            base_url=cfg["base_url"],
            timeout=float(cfg.get("timeout", 180)),
            max_retries=0,
            http_client=httpx.Client(trust_env=False, timeout=float(cfg.get("timeout", 180))),
        )

        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.raw_log_path = raw_log_path
        os.makedirs(os.path.dirname(raw_log_path), exist_ok=True)
        self._lock = threading.Lock()
        self._raw_fh = open(raw_log_path, "a", encoding="utf-8")

        self.stats = {
            "api_calls": 0,
            "cache_hits": 0,
            "api_fail": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "reasoning_tokens": 0,
            "cost_cny": 0.0,
            "latency_s": 0.0,
        }

    # ------------------------------------------------------------------ 内部工具
    def _cache_key(self, messages, tag):
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_tokens": self.max_tokens,
                "reasoning_effort": self.reasoning_effort,
                "messages": messages,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256((tag + "|" + payload).encode("utf-8")).hexdigest()

    def _log_raw(self, record):
        with self._lock:
            self._raw_fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._raw_fh.flush()

    def _accumulate(self, usage, latency, cached=False):
        with self._lock:
            if cached:
                self.stats["cache_hits"] += 1
                return
            self.stats["api_calls"] += 1
            self.stats["latency_s"] += latency
            tin = int(usage.get("prompt_tokens", 0) or 0)
            tout = int(usage.get("completion_tokens", 0) or 0)
            self.stats["tokens_in"] += tin
            self.stats["tokens_out"] += tout
            self.stats["reasoning_tokens"] += int(usage.get("reasoning_tokens", 0) or 0)
            self.stats["cost_cny"] += (
                tin * self.price_in + tout * self.price_out
            ) / 1_000_000

    # ------------------------------------------------------------------ 对外接口
    def complete(self, messages, tag, sample_id):
        """返回 dict: text, usage, cached, api_error, attempts, latency_s"""
        key = self._cache_key(messages, tag)
        cache_path = os.path.join(self.cache_dir, key + ".json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                self._accumulate(cached.get("usage", {}), 0.0, cached=True)
                self._log_raw(
                    {
                        "sample_id": sample_id,
                        "tag": tag,
                        "messages": messages,
                        "response": cached["text"],
                        "reasoning_content": cached.get("reasoning", ""),
                        "usage": cached.get("usage", {}),
                        "cached": True,
                        "latency_s": 0.0,
                        "attempts": 0,
                    }
                )
                return {
                    "text": cached["text"],
                    "reasoning": cached.get("reasoning", ""),
                    "usage": cached.get("usage", {}),
                    "cached": True,
                    "api_error": None,
                    "attempts": 0,
                    "latency_s": 0.0,
                    "finish_reason": cached.get("finish_reason"),
                }
            except Exception:
                pass  # 缓存损坏则重新请求

        last_err = None
        for attempt in range(self.max_retries + 1):
            t0 = time.time()
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                latency = time.time() - t0
                msg = resp.choices[0].message
                text = msg.content or ""
                reasoning = getattr(msg, "reasoning_content", None) or ""
                usage = {
                    "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                }
                details = getattr(resp.usage, "completion_tokens_details", None)
                usage["reasoning_tokens"] = (
                    int(getattr(details, "reasoning_tokens", 0) or 0) if details else 0
                )
                finish_reason = getattr(resp.choices[0], "finish_reason", None)

                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "text": text,
                            "reasoning": reasoning,
                            "usage": usage,
                            "finish_reason": finish_reason,
                        },
                        f,
                        ensure_ascii=False,
                    )

                self._accumulate(usage, latency)
                self._log_raw(
                    {
                        "sample_id": sample_id,
                        "tag": tag,
                        "messages": messages,
                        "response": text,
                        "reasoning_content": reasoning,
                        "usage": usage,
                        "cached": False,
                        "latency_s": round(latency, 3),
                        "attempts": attempt + 1,
                        "finish_reason": finish_reason,
                    }
                )
                return {
                    "text": text,
                    "reasoning": reasoning,
                    "usage": usage,
                    "cached": False,
                    "api_error": None,
                    "attempts": attempt + 1,
                    "latency_s": latency,
                    "finish_reason": finish_reason,
                }
            except Exception as e:  # noqa: BLE001
                last_err = f"{type(e).__name__}: {e}"
                if attempt < self.max_retries:
                    sleep = self.retry_base_sleep * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(sleep)

        with self._lock:
            self.stats["api_fail"] += 1
        self._log_raw(
            {
                "sample_id": sample_id,
                "tag": tag,
                "messages": messages,
                "response": None,
                "usage": {},
                "cached": False,
                "latency_s": 0.0,
                "attempts": self.max_retries + 1,
                "api_error": last_err,
            }
        )
        return {
            "text": "",
            "reasoning": "",
            "usage": {},
            "cached": False,
            "api_error": last_err,
            "attempts": self.max_retries + 1,
            "latency_s": 0.0,
            "finish_reason": None,
        }

    def close(self):
        try:
            self._raw_fh.close()
        except Exception:
            pass

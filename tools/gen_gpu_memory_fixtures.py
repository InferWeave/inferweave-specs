#!/usr/bin/env python3
"""Generate the four iw.gpu-memory/1 contract fixtures (contracts/gpu-memory/)
with exact byte arithmetic, and check the spec 46 §3.1 / §4 invariants on every
GPU before writing. The files are shared byte-for-byte with the reference
implementation (InferWeave/inferweave contracts/gpu-memory/) and the gateway
consumer, so they are written in canonical form: keys sorted, 2-space indent,
UTF-8, one trailing newline.

Run: python3 -I tools/gen_gpu_memory_fixtures.py contracts/gpu-memory"""
import json, sys, os

GiB = 1024 ** 3
MiB = 1024 ** 2

def q(b, basis="measured", source=None, conf=None, note=None):
    d = {"bytes": int(b), "basis": basis}
    if source: d["source"] = source
    if conf: d["confidence"] = conf
    if note: d["note"] = note
    return d

def unk(basis="unknown", note=None):
    d = {"basis": basis}
    if note: d["note"] = note
    return d

WEAK = ["measured", "derived", "declared", "estimated"]
def weakest(*qs):
    """Basis of an arithmetic result: 'estimated' if any input is estimated,
    otherwise 'derived' (policy constants are exact, measured inputs exact)."""
    ranks = [WEAK.index(x["basis"]) for x in qs if "bytes" in x]
    if not ranks: return "unknown"
    return "estimated" if max(ranks) == 3 else "derived"

def finish_gpu(g, placement_res=0, compose=True):
    """Compute attributed/unattributed/nodeSafe/safe per spec. Returns g."""
    p = g["physical"]
    if "bytes" not in p.get("used", {}) or g["telemetry"]["status"] != "fresh":
        g["nodeSafeSchedulable"] = unk(note="telemetry not fresh")
        if compose:
            g["safeSchedulable"] = unk(note="telemetry not fresh")
        return g
    lg = g["logical"]
    reserves = sum(v["bytes"] for k, v in lg.items() if k != "placementReservations" and "bytes" in v)
    free = p["free"]["bytes"]
    node_safe = max(0, free - reserves)
    g["nodeSafeSchedulable"] = q(node_safe, weakest(p["free"], *[v for v in lg.values()]), "iw-ledger")
    if compose:
        safe = max(0, node_safe - placement_res)
        g["safeSchedulable"] = q(safe, weakest(p["free"], *[v for v in lg.values()]), "iw-ledger")
    return g

def check(doc, name):
    nodes = doc.get("nodes") or [doc]
    for n in nodes:
        for g in n["gpus"]:
            p = g["physical"]
            if "bytes" in p.get("used", {}) and "bytes" in p.get("free", {}):
                tot = p["total"]["bytes"]
                assert abs(p["used"]["bytes"] + p["free"]["bytes"] - tot) <= 0.02 * tot, (name, g["resourceId"], "used+free")
                cats = sum(v["bytes"] for v in g.get("categories", {}).values() if "bytes" in v)
                assert "unattributed" in g, (name, "unattributed must be present when used known")
                ua = g["unattributed"]["bytes"]
                assert g["attributed"]["bytes"] + ua == p["used"]["bytes"], (name, g["resourceId"], "attr+unattr")
                if g.get("categories"):
                    assert cats == g["attributed"]["bytes"], (name, g["resourceId"], "cats==attributed", cats, g["attributed"]["bytes"])
                # logical never inside physical: nothing to sum, but safe <= free
                if "bytes" in g.get("safeSchedulable", {}):
                    assert g["safeSchedulable"]["bytes"] <= p["free"]["bytes"]
            # unknown must not carry bytes
            def walk(o):
                if isinstance(o, dict):
                    if o.get("basis") in ("unknown", "unsupported"):
                        assert "bytes" not in o, (name, o)
                    for v in o.values(): walk(v)
                elif isinstance(o, list):
                    for v in o: walk(v)
            walk(g)

def node_report(node_id, gw, gpus, runtimes, allocations, ownership, anomalies=None, seq=1842):
    return {
        "schema": "iw.gpu-memory.report/1",
        "producerEpoch": "ep_" + node_id[-6:] + "a1",
        "sequence": seq,
        "observedAt": "2026-10-08T14:31:05Z",
        "origin": {"gatewayId": gw, "nodeId": node_id, "via": [gw] if gw else []},
        "ownership": ownership,
        "policy": {"safetyMarginPercent": 5, "accountingTolerancePercent": 2, "telemetryIntervalSecs": 5},
        "truncated": False,
        "gpus": gpus, "runtimes": runtimes, "allocations": allocations,
        "anomalies": anomalies or [],
    }

def fleet(gw, nodes, reservations, mode="observe", seq=913, peers=None):
    return {
        "schema": "iw.gpu-memory.fleet/1",
        "gatewayId": gw, "producerEpoch": "ep_" + gw[-4:] + "0f", "sequence": seq,
        "generatedAt": "2026-10-08T14:31:07Z",
        "authority": {"rebalancer": True, "mode": mode},
        "nodes": nodes, "reservations": reservations, "peers": peers or [],
    }

# ---------------------------------------------------------------- fixture 1
def f1():
    """Spec §5 worked example, B200-like 96 GiB, llama.cpp primary + whisper
    opportunistic + foreign process + one pending PACK reservation."""
    gw, node = "gw_fry-rust", "node_b200-01"
    dev = "GPU-5f1e0c2a-7b7d-4c55-9d0e-3b3e2a1c9f01"
    rid = f"gpu:{gw}/{node}/{dev}"
    total = 96 * GiB
    prim_w, prim_kv, prim_pc, prim_ws = 58 * GiB, 10 * GiB, 3 * GiB, 3 * GiB
    wh_w, wh_ws = 3 * GiB, 1 * GiB
    other = 2 * GiB
    used = prim_w + prim_kv + prim_pc + prim_ws + wh_w + wh_ws + other  # 80 GiB
    free = total - used
    prim_total = prim_w + prim_kv + prim_pc + prim_ws
    wh_total = wh_w + wh_ws
    kvpt = 32768  # bytes/token (illustrative q8 KV)
    slot_tokens = [61440, 40960, 28672, None]
    slots = []
    for i, t in enumerate(slot_tokens):
        s = {"slotId": i, "state": "active" if t else "idle", "maxContextTokens": 81920}
        if t:
            s.update({"contextTokens": t,
                      "kvCache": q(t * kvpt, "estimated", "llama.cpp-slots", "low",
                                   "tokens x kvPerToken; llama.cpp has no per-slot byte counter"),
                      "requestAgeMs": [41000, 12000, 230000][i],
                      "lastActivityAt": "2026-10-08T14:31:04Z", "tokensPerSec": [38.2, 41.0, 36.5][i]})
        else:
            s.update({"contextTokens": 0, "kvCache": q(0, "estimated", "llama.cpp-slots", "low", "idle slot: pool reserved, no tokens")})
        slots.append(s)
    g = {
        "resourceId": rid, "deviceId": dev, "topologyGpuId": dev, "deviceKeyStable": True, "index": 0,
        "vendor": "nvidia", "name": "NVIDIA B200 (illustrative 96 GiB per spec §5)",
        "driver": {"name": "nvidia", "version": "580.65.06", "runtime": "cuda-13.0"},
        "authority": "owned",
        "telemetry": {"status": "fresh", "observedAt": "2026-10-08T14:31:05Z", "ageMs": 1200,
                      "sources": ["nvidia-smi", "nvidia-smi-compute-apps", "llama.cpp-props", "llama.cpp-slots", "torch-allocator"]},
        "physical": {"total": q(total, source="nvidia-smi"), "used": q(used, source="nvidia-smi"), "free": q(free, source="nvidia-smi")},
        "categories": {
            "weights": q(prim_w + wh_w, "estimated", "iw-registry", "medium", "primary GGUF size 58 GiB + whisper declared 3 GiB"),
            "kvCache": q(prim_kv, "derived", "llama.cpp-props", "medium", "nCtx 327680 x kvPerToken 32768"),
            "prefixCache": q(prim_pc, "estimated", "llama.cpp-props", "low", "--cache-ram host/device split estimate"),
            "workspace": q(prim_ws + wh_ws, "derived", "nvidia-smi-compute-apps", "medium", "process total minus other categories"),
            "other": q(other, "measured", "nvidia-smi-compute-apps", "high", "non-InferWeave process (pid 2231 python)"),
        },
        "attributed": q(used, "estimated"),
        "unattributed": q(0, "derived", note="per-process totals sum to card used"),
        "byClass": {"primary": q(prim_total, "measured", "nvidia-smi-compute-apps"),
                    "opportunistic": q(wh_total, "measured", "nvidia-smi-compute-apps")},
        "logical": {
            "kvGrowthReserve": q(0, "declared", note="llama.cpp KV pool preallocated; growth is pool occupancy, see kvPool"),
            "runtimeGrowthReserve": q(2 * GiB, "declared", "config", note="whisper workspacePeak 3 GiB - current 1 GiB"),
            "safetyHeadroom": q(4 * GiB, "declared", "config", note="spec §5 example value 4 GiB (operator override; 5% default would be 4.8 GiB)"),
            "placementReservations": q(4 * GiB, "declared", "iw-ledger", note="rv for bge-m3 PACK, pending"),
        },
        "pressure": {"state": "comfortable", "since": "2026-10-08T14:02:00Z",
                     "headroom": None, "kvPoolOccupancy": 0.40,
                     "reasons": ["free-after-growth 14 GiB = 3.5x safety"]},
        "eligibility": {"opportunistic": True, "reasons": []},
    }
    finish_gpu(g, placement_res=4 * GiB)
    g["pressure"]["headroom"] = g["safeSchedulable"]
    runtimes = [
        {"runtimeInstanceId": f"{node}-llama.cpp-0", "deployment": "dep_" + "a" * 64,
         "modelId": "qwen3.8-27b-modality-text-quant-q8_k_xl", "adapter": "llama.cpp", "adapterVersion": "b6402",
         "placementClass": "primary", "evictable": False, "migrationSupported": False,
         "placementGroup": {"gpus": [rid], "topology": "single", "tensorParallel": 1, "pipelineParallel": 1, "shardMovable": False},
         "perGpu": [{"resourceId": rid, "weights": q(prim_w, "estimated", "iw-registry"), "kvCache": q(prim_kv, "derived", "llama.cpp-props"),
                     "workspace": q(prim_ws, "derived", "nvidia-smi-compute-apps"), "physicalTotal": q(prim_total, "measured", "nvidia-smi-compute-apps")}],
         "total": q(prim_total, "measured", "nvidia-smi-compute-apps"),
         "kvPool": {"preallocated": True, "capacityTokens": 327680, "usedTokens": sum(t for t in slot_tokens if t),
                    "usageRatio": {"value": round(sum(t for t in slot_tokens if t) / 327680, 4), "basis": "derived", "source": "llama.cpp-slots"}},
         "slots": {"support": "per-slot-estimated", "items": slots},
         "adapterResources": {"accelerators": ["cuda", "rocm", "vulkan"], "startupSecs": 95, "eviction": "drain-then-unload", "dynamicGrowth": "preallocated", "maxConcurrency": 4},
         "lastActivityAt": "2026-10-08T14:31:04Z", "activeRequests": 3},
        {"runtimeInstanceId": f"{node}-whisper-0", "deployment": "dep_" + "b" * 64,
         "modelId": "whisper-large-v3-turbo", "adapter": "whisper", "adapterVersion": "faster-whisper-1.2",
         "placementClass": "opportunistic", "evictable": True, "migrationSupported": True,
         "placementGroup": {"gpus": [rid], "topology": "single", "tensorParallel": 1, "pipelineParallel": 1, "shardMovable": False},
         "perGpu": [{"resourceId": rid, "weights": q(wh_w, "declared", "config"), "workspace": q(wh_ws, "derived", "torch-allocator"),
                     "logicalReserve": q(2 * GiB, "declared", "config"), "physicalTotal": q(wh_total, "measured", "nvidia-smi-compute-apps")}],
         "total": q(wh_total, "measured", "nvidia-smi-compute-apps"),
         "slots": {"support": "unsupported"},
         "adapterResources": {"accelerators": ["cuda"], "expectedWeights": q(3 * GiB, "declared", "config"),
                              "workspaceMin": q(512 * MiB, "declared", "config"), "workspacePeak": q(3 * GiB, "declared", "config"),
                              "startupSecs": 20, "eviction": "drain-then-unload", "dynamicGrowth": "allocator", "maxConcurrency": 2},
         "lastActivityAt": "2026-10-08T14:29:40Z", "activeRequests": 0},
    ]
    allocations = [
        {"allocationId": f"al_{node}_{dev[:13]}_41122", "resourceId": rid, "runtimeInstanceId": f"{node}-llama.cpp-0",
         "modelId": "qwen3.8-27b-modality-text-quant-q8_k_xl", "category": "runtime-total",
         "physical": q(prim_total, "measured", "nvidia-smi-compute-apps", note="MiB resolution"),
         "placementClass": "primary", "evictable": False, "intended": True, "observedAt": "2026-10-08T14:31:05Z",
         "meta": {"processName": "llama-server"}},
        {"allocationId": f"al_{node}_{dev[:13]}_41377", "resourceId": rid, "runtimeInstanceId": f"{node}-whisper-0",
         "modelId": "whisper-large-v3-turbo", "category": "runtime-total",
         "physical": q(wh_total, "measured", "nvidia-smi-compute-apps", note="MiB resolution"),
         "reservation": q(2 * GiB, "declared", "config"),
         "placementClass": "opportunistic", "evictable": True, "intended": True, "observedAt": "2026-10-08T14:31:05Z",
         "meta": {"processName": "python3"}},
        {"allocationId": f"al_{node}_{dev[:13]}_2231", "resourceId": rid, "category": "foreign-process",
         "physical": q(other, "measured", "nvidia-smi-compute-apps", note="MiB resolution"),
         "placementClass": "primary", "evictable": False, "intended": None, "observedAt": "2026-10-08T14:31:05Z",
         "meta": {"processName": "python"}},
    ]
    n = node_report(node, gw, [g], runtimes, allocations,
                    {"manager": "standalone", "allocationState": "active", "actionAuthority": "origin-gateway"})
    res = [{"reservationId": f"rv_d-1759933865-17-a1b2_{dev[:13]}", "decisionId": "d-1759933865-17-a1b2",
            "owner": {"gatewayId": gw, "component": "autoscaler"}, "kind": "placement", "resourceId": rid,
            "placementGroupId": "pg_d-1759933865-17-a1b2", "modelId": "bge-m3-embedding", "placementClass": "opportunistic",
            "requestedBytes": 4 * GiB, "effectiveBytes": 4 * GiB,
            "createdAt": "2026-10-08T14:30:50Z", "expiresAt": "2026-10-08T15:30:50Z", "state": "pending",
            "reason": "pack: nodeSafe=10.0GiB need=4.0GiB (shadow would be recorded only)"}]
    return fleet(gw, [n], res, mode="on")

# ---------------------------------------------------------------- fixture 2
def f2():
    """vLLM TP=4 across 4x A100-80GB inside a Slurm allocation (hive-like)."""
    gw, node = "gw_hive-rust", "node_g7-deepseek"
    total = 81920 * MiB
    w, kv, graphs, ovh = 40 * GiB, 30 * GiB, int(1.5 * GiB), 2 * GiB
    used = w + kv + graphs + ovh
    gpus, per, rids = [], [], []
    for i in range(4):
        dev = f"GPU-0a7e{i}c11-2f4d-4e8a-9b1c-7d6e5f4a3b2{i}"
        rid = f"gpu:{gw}/{node}/{dev}"
        rids.append(rid)
        g = {"resourceId": rid, "deviceId": dev, "topologyGpuId": dev, "deviceKeyStable": True, "index": i,
             "vendor": "nvidia", "name": "NVIDIA A100-SXM4-80GB",
             "driver": {"name": "nvidia", "version": "550.127.05", "runtime": "cuda-12.4"}, "authority": "owned",
             "telemetry": {"status": "fresh", "observedAt": "2026-10-08T14:31:03Z", "ageMs": 2100,
                           "sources": ["nvidia-smi", "nvidia-smi-compute-apps", "vllm-metrics"]},
             "physical": {"total": q(total, source="nvidia-smi"), "used": q(used, source="nvidia-smi"), "free": q(total - used, source="nvidia-smi")},
             "categories": {
                 "weights": q(w, "estimated", "iw-registry", note="checkpoint bytes / TP 4"),
                 "kvCache": q(kv, "derived", "vllm-metrics", note="num_gpu_blocks x block_bytes from cache_config_info"),
                 "executionGraphs": q(graphs, "estimated", "iw-resource-profile", note="RP profile peak, CUDA graphs captured"),
                 "runtimeOverhead": q(ovh, "derived", "nvidia-smi-compute-apps", note="process total - weights - kv - graphs"),
             },
             "attributed": q(used, "estimated"),
             "unattributed": q(0, "derived"),
             "byClass": {"primary": q(used, "measured", "nvidia-smi-compute-apps")},
             "logical": {"kvGrowthReserve": q(0, "declared", note="vLLM KV pool preallocated (gpu_memory_utilization 0.90)"),
                         "safetyHeadroom": q(4 * GiB, "declared", "config", note="5% of 80 GiB"),
                         "measurementUncertainty": q(512 * MiB, "derived", note="graphs estimate +-0.5 GiB"),
                         "placementReservations": q(0, "declared", "iw-ledger")},
             "pressure": {"state": "constrained", "since": "2026-10-08T09:02:11Z", "previous": "comfortable",
                          "kvPoolOccupancy": 0.42, "reasons": ["free-after-growth 6.5 GiB = 1.6x safety; preallocated runtime, no growth exposure"]},
             "eligibility": {"opportunistic": False, "reasons": ["primary-restart-reserve-missing", "opportunistic-disabled"]}}
        finish_gpu(g, placement_res=0)
        g["pressure"]["headroom"] = g["safeSchedulable"]
        gpus.append(g)
        per.append({"resourceId": rid, "weights": q(w, "estimated", "iw-registry"), "kvCache": q(kv, "derived", "vllm-metrics"),
                    "workspace": q(graphs + ovh, "derived", "nvidia-smi-compute-apps"), "physicalTotal": q(used, "measured", "nvidia-smi-compute-apps")})
    rt = {"runtimeInstanceId": f"{node}-vllm-0", "deployment": "dep_" + "c" * 64,
          "modelId": "deepseek-v4.1-modality-text-quant-fp8", "adapter": "vllm", "adapterVersion": "0.11.0",
          "placementClass": "primary", "evictable": False, "migrationSupported": False,
          "placementGroup": {"gpus": rids, "topology": "tensor", "tensorParallel": 4, "pipelineParallel": 1, "shardMovable": False},
          "perGpu": per, "total": q(used * 4, "measured", "nvidia-smi-compute-apps"),
          "kvPool": {"preallocated": True, "usageRatio": {"value": 0.42, "basis": "measured", "source": "vllm-metrics"}},
          "slots": {"support": "runtime-total"},
          "adapterResources": {"accelerators": ["cuda"], "startupSecs": 540, "eviction": "drain-then-unload", "dynamicGrowth": "preallocated", "maxConcurrency": 64},
          "lastActivityAt": "2026-10-08T14:31:02Z", "activeRequests": 11}
    allocs = [{"allocationId": f"al_{node}_{r.split('/')[-1][:13]}_99812", "resourceId": r, "runtimeInstanceId": rt["runtimeInstanceId"],
               "modelId": rt["modelId"], "category": "runtime-total", "physical": q(used, "measured", "nvidia-smi-compute-apps", note="MiB resolution"),
               "placementClass": "primary", "evictable": False, "intended": True, "observedAt": "2026-10-08T14:31:03Z",
               "meta": {"processName": "python3 (vllm worker)"}} for r in rids]
    n = node_report(node, gw, gpus, [rt], allocs,
                    {"manager": "slurm", "allocationId": "4823117", "allocationState": "active",
                     "allocationEndsAt": "2026-10-09T02:00:00Z", "actionAuthority": "origin-gateway"}, seq=77120)
    return fleet(gw, [n], [], mode="observe", seq=40211,
                 peers=[])

# ---------------------------------------------------------------- fixture 3
def f3():
    """beast: 2x AMD Radeon AI PRO R9700 (32 GiB), ROCm, llama.cpp layer-split
    across both cards, per-slot unsupported, display compositor on GPU1.
    Standalone (no Slurm), reported via a workstation gateway, relayed to Fry."""
    gw, node = "gw_beast", "node_beast"
    total = 32 * GiB
    specs = [  # (weights, kv, workspace, other)
        (14 * GiB, 9 * GiB, int(1.5 * GiB), 0),
        (13 * GiB, 9 * GiB, int(1.25 * GiB), 768 * MiB),
    ]
    gpus, per, rids = [], [], []
    for i, (w, kv, ws, oth) in enumerate(specs):
        dev = f"amd-0x{(0x7a3c10e5 + i):08x}"  # amdgpu unique_id
        rid = f"gpu:{gw}/{node}/{dev}"
        rids.append(rid)
        proc = w + kv + ws
        used = proc + oth
        cats = {"weights": q(w, "estimated", "iw-registry", note="GGUF tensor split share"),
                "kvCache": q(kv, "derived", "llama.cpp-props", note="nCtx x kvPerToken / 2 devices"),
                "workspace": q(ws, "derived", "drm-fdinfo", note="process drm-memory-vram minus weights+kv")}
        if oth:
            cats["other"] = q(oth, "measured", "drm-fdinfo", note="gnome-shell / Xwayland")
        g = {"resourceId": rid, "deviceId": dev, "topologyGpuId": dev, "deviceKeyStable": True, "index": i,
             "vendor": "amd", "name": "AMD Radeon AI PRO R9700",
             "driver": {"name": "amdgpu", "version": "6.14", "runtime": "rocm-7.0.1"}, "authority": "owned",
             "telemetry": {"status": "fresh", "observedAt": "2026-10-08T14:31:04Z", "ageMs": 900,
                           "sources": ["sysfs", "drm-fdinfo", "rocm-smi", "llama.cpp-props"]},
             "physical": {"total": q(total, source="sysfs", note="mem_info_vram_total, rounded down"),
                          "used": q(used, source="sysfs", note="mem_info_vram_used, rounded up"),
                          "free": q(total - used, "derived", "sysfs")},
             "categories": cats,
             "attributed": q(used, "estimated"),
             "unattributed": q(0, "derived"),
             "byClass": {"primary": q(proc, "measured", "drm-fdinfo")},
             "logical": {"kvGrowthReserve": q(0, "declared", note="llama.cpp KV preallocated"),
                         "safetyHeadroom": q(int(total * 0.05) // MiB * MiB, "declared", "config"),
                         "placementReservations": q(0, "declared", "iw-ledger")},
             "pressure": {"state": "comfortable", "since": "2026-10-08T08:00:00Z", "kvPoolOccupancy": None,
                          "reasons": []},
             "eligibility": {"opportunistic": False, "reasons": ["opportunistic-disabled"]}}
        finish_gpu(g)
        g["pressure"]["headroom"] = g["safeSchedulable"]
        del g["pressure"]["kvPoolOccupancy"]  # unknown: /slots disabled -> absent, never 0
        gpus.append(g)
        per.append({"resourceId": rid, "weights": q(w, "estimated", "iw-registry"), "kvCache": q(kv, "derived", "llama.cpp-props"),
                    "workspace": q(ws, "derived", "drm-fdinfo"), "physicalTotal": q(proc, "measured", "drm-fdinfo")})
    rt = {"runtimeInstanceId": f"{node}-llama.cpp-0", "deployment": "dep_" + "d" * 64,
          "modelId": "qwen3.8-27b-modality-text-quant-q8_k_xl", "adapter": "llama.cpp", "adapterVersion": "b6402-rocm",
          "placementClass": "primary", "evictable": False, "migrationSupported": False,
          "placementGroup": {"gpus": rids, "topology": "layer-split", "tensorParallel": 1, "pipelineParallel": 2, "shardMovable": False},
          "perGpu": per, "total": q(sum(p["physicalTotal"]["bytes"] for p in per), "measured", "drm-fdinfo"),
          "kvPool": {"preallocated": True, "capacityTokens": 262144,
                     "usageRatio": unk("unsupported", "engine started without --slots; no occupancy endpoint")},
          "slots": {"support": "unsupported"},
          "adapterResources": {"accelerators": ["rocm", "vulkan"], "startupSecs": 70, "eviction": "drain-then-unload", "dynamicGrowth": "preallocated", "maxConcurrency": 2},
          "activeRequests": 1}
    allocs = []
    for (w, kv, ws, oth), r in zip(specs, rids):
        allocs.append({"allocationId": f"al_{node}_{r.split('/')[-1]}_3120", "resourceId": r, "runtimeInstanceId": rt["runtimeInstanceId"],
                       "modelId": rt["modelId"], "category": "runtime-total", "physical": q(w + kv + ws, "measured", "drm-fdinfo"),
                       "placementClass": "primary", "evictable": False, "intended": None, "observedAt": "2026-10-08T14:31:04Z",
                       "meta": {"processName": "llama-server"}})
        if oth:
            allocs.append({"allocationId": f"al_{node}_{r.split('/')[-1]}_1877", "resourceId": r, "category": "foreign-process",
                           "physical": q(oth, "measured", "drm-fdinfo"), "placementClass": "primary", "evictable": False,
                           "observedAt": "2026-10-08T14:31:04Z", "meta": {"processName": "gnome-shell"}})
    n = node_report(node, gw, gpus, [rt], allocs, {"manager": "standalone", "allocationState": "active", "actionAuthority": "origin-gateway"}, seq=5531)
    f = fleet(gw, [n], [], mode="observe", seq=2210)
    # as relayed through Fry: via path grows; Fry is NOT the authority
    n["origin"]["via"] = ["gw_beast", "gw_fry"]
    return f

# ---------------------------------------------------------------- fixture 4
def f4():
    """Stale telemetry + accounting anomaly + draining Slurm allocation +
    a visible GPU owned by another job (not schedulable)."""
    gw, node = "gw_hive-rust", "node_g3-glm"
    total = 81920 * MiB
    gpus = []
    # GPU0: stale
    d0 = "GPU-11aa22bb-0000-4000-8000-00000000c0de"
    r0 = f"gpu:{gw}/{node}/{d0}"
    g0 = {"resourceId": r0, "deviceId": d0, "topologyGpuId": d0, "deviceKeyStable": True, "index": 0,
          "vendor": "nvidia", "name": "NVIDIA A100-SXM4-80GB", "authority": "owned",
          "telemetry": {"status": "stale", "observedAt": "2026-10-08T14:27:01Z", "ageMs": 244000, "sources": ["nvidia-smi"]},
          "physical": {"total": q(total, source="nvidia-smi"), "used": unk(note="last reading 244 s old; not carried forward"),
                       "free": unk(note="last reading 244 s old; not carried forward")},
          "logical": {"safetyHeadroom": q(4 * GiB, "declared", "config")},
          "pressure": {"state": "unknown", "since": "2026-10-08T14:27:31Z", "previous": "comfortable", "reasons": ["telemetry-stale"]},
          "eligibility": {"opportunistic": False, "reasons": ["telemetry-stale", "allocation-draining"]}}
    finish_gpu(g0)
    # GPU1: anomaly
    d1 = "GPU-11aa22bb-0000-4000-8000-00000000c0df"
    r1 = f"gpu:{gw}/{node}/{d1}"
    used1 = 74 * GiB
    att1 = 52 * GiB
    g1 = {"resourceId": r1, "deviceId": d1, "topologyGpuId": d1, "deviceKeyStable": True, "index": 1,
          "vendor": "nvidia", "name": "NVIDIA A100-SXM4-80GB", "authority": "owned",
          "telemetry": {"status": "fresh", "observedAt": "2026-10-08T14:31:05Z", "ageMs": 1500, "sources": ["nvidia-smi", "nvidia-smi-compute-apps"]},
          "physical": {"total": q(total, source="nvidia-smi"), "used": q(used1, source="nvidia-smi"), "free": q(total - used1, source="nvidia-smi")},
          "categories": {"weights": q(38 * GiB, "estimated", "iw-registry"),
                         "kvCache": q(12 * GiB, "derived", "llama.cpp-props"),
                         "workspace": q(2 * GiB, "derived", "nvidia-smi-compute-apps")},
          "attributed": q(att1, "estimated"),
          "unattributed": q(used1 - att1, "derived", note="card used minus all per-process totals"),
          "byClass": {"primary": q(att1, "measured", "nvidia-smi-compute-apps")},
          "logical": {"safetyHeadroom": q(4 * GiB, "declared", "config"), "placementReservations": q(0, "declared", "iw-ledger")},
          "pressure": {"state": "constrained", "since": "2026-10-08T14:22:40Z", "previous": "comfortable",
                       "reasons": ["free-after-growth 6 GiB = 1.5x safety", "unattributed 22 GiB > tolerance"]},
          "eligibility": {"opportunistic": False, "reasons": ["anomaly", "allocation-draining"]}}
    finish_gpu(g1)
    g1["pressure"]["headroom"] = g1["safeSchedulable"]
    # GPU2: visible but owned by another Slurm job
    d2 = "GPU-11aa22bb-0000-4000-8000-00000000c0e0"
    r2 = f"gpu:{gw}/{node}/{d2}"
    used2 = 20 * GiB
    g2 = {"resourceId": r2, "deviceId": d2, "topologyGpuId": d2, "deviceKeyStable": True, "index": 2,
          "vendor": "nvidia", "name": "NVIDIA A100-SXM4-80GB", "authority": "not-owned",
          "telemetry": {"status": "fresh", "observedAt": "2026-10-08T14:31:05Z", "ageMs": 1500, "sources": ["nvidia-smi"]},
          "physical": {"total": q(total, source="nvidia-smi"), "used": q(used2, source="nvidia-smi"), "free": q(total - used2, source="nvidia-smi")},
          "attributed": q(0, "derived", note="no InferWeave process; foreign job not attributable"),
          "unattributed": q(used2, "derived"),
          "logical": {},
          "nodeSafeSchedulable": q(0, "declared", note="not owned: belongs to another Slurm allocation (spec §36)"),
          "safeSchedulable": q(0, "declared", note="not owned: belongs to another Slurm allocation (spec §36)"),
          "pressure": {"state": "unknown", "reasons": ["not-owned"]},
          "eligibility": {"opportunistic": False, "reasons": ["not-owned"]}}
    gpus = [g0, g1, g2]
    rt = {"runtimeInstanceId": f"{node}-llama.cpp-0", "deployment": "dep_" + "e" * 64,
          "modelId": "glm-4.7-modality-text-quant-q4_k_m", "adapter": "llama.cpp", "adapterVersion": "b6380",
          "placementClass": "normal", "evictable": False, "migrationSupported": False,
          "placementGroup": {"gpus": [r0, r1], "topology": "layer-split", "tensorParallel": 1, "pipelineParallel": 2, "shardMovable": False},
          "perGpu": [{"resourceId": r0, "physicalTotal": unk(note="stale")},
                     {"resourceId": r1, "weights": q(38 * GiB, "estimated", "iw-registry"), "kvCache": q(12 * GiB, "derived", "llama.cpp-props"),
                      "workspace": q(2 * GiB, "derived", "nvidia-smi-compute-apps"), "physicalTotal": q(att1, "measured", "nvidia-smi-compute-apps")}],
          "total": unk(note="one participating GPU stale"),
          "kvPool": {"preallocated": True, "usageRatio": {"value": 0.18, "basis": "derived", "source": "llama.cpp-slots"}},
          "slots": {"support": "per-slot-estimated", "items": [
              {"slotId": 0, "state": "active", "contextTokens": 20480, "maxContextTokens": 131072,
               "kvCache": q(20480 * 49152, "estimated", "llama.cpp-slots", "low")},
              {"slotId": 1, "state": "idle", "contextTokens": 0, "maxContextTokens": 131072,
               "kvCache": q(0, "estimated", "llama.cpp-slots", "low")}]},
          "activeRequests": 1}
    allocs = [{"allocationId": f"al_{node}_GPU-11aa22bb_0001", "resourceId": r1, "runtimeInstanceId": rt["runtimeInstanceId"],
               "modelId": rt["modelId"], "category": "runtime-total", "physical": q(att1, "measured", "nvidia-smi-compute-apps"),
               "placementClass": "normal", "evictable": False, "intended": True, "observedAt": "2026-10-08T14:31:05Z",
               "meta": {"processName": "llama-server"}}]
    anomalies = [{"anomalyId": "an_c0df_ep_g3glma1_77", "resourceId": r1, "kind": "unattributed-over-tolerance",
                  "measuredBytes": used1 - att1, "toleranceBytes": int(total * 0.02),
                  "firstSeenAt": "2026-10-08T14:22:35Z", "lastSeenAt": "2026-10-08T14:31:05Z", "consecutive": 103,
                  "detail": "22 GiB on card not owned by any process nvidia-smi lists; candidates: leaked context of a crashed engine, MPS server, process in another PID namespace"}]
    n = node_report(node, gw, gpus, [rt], allocs,
                    {"manager": "slurm", "allocationId": "4822960", "allocationState": "draining",
                     "allocationEndsAt": "2026-10-08T14:41:00Z", "actionAuthority": "origin-gateway"}, anomalies, seq=9921)
    return fleet(gw, [n], [], mode="observe", seq=40212,
                 peers=[{"gatewayId": "gw_beast", "status": "stale", "receivedAgeMs": 184000, "capabilities": ["iw.gpu-memory/1"]}])

def main(out):
    fx = {
        "01-b200-primary-whisper-pack.fleet.json": f1(),
        "02-a100x4-vllm-tp4-slurm.fleet.json": f2(),
        "03-r9700x2-rocm-layer-split-no-slots.fleet.json": f3(),
        "04-stale-anomaly-draining-notowned.fleet.json": f4(),
    }
    for name, doc in fx.items():
        check(doc, name)
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            # Canonical bytes: sorted keys, 2-space indent, UTF-8 (not \u escapes),
            # trailing newline. Producers in any language reproduce these bytes
            # by sorting object keys; struct field order is not part of the contract.
            json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print("ok", name, os.path.getsize(os.path.join(out, name)), "bytes")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")

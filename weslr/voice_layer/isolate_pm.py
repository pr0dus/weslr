#!/usr/bin/env python3
"""Isolate presence_monitor test"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time as t
import weslr.voice_layer

def get_mod(name):
    return sys.modules[f"weslr.voice_layer.{name}"]

pres_mod = get_mod("presence_monitor")
PresenceMonitor = pres_mod.PresenceMonitor

print("Creating PresenceMonitor...")
t0 = t.time()
pm = PresenceMonitor(tenant_id="test")
print(f"Created in {t.time()-t0:.2f}s, calling signal_arrival...")
sys.stdout.flush()
t0 = t.time()
pm.signal_arrival()
print(f"signal_arrival done in {t.time()-t0:.2f}s")
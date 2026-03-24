"""Concurrent load test: fire 20-30 analyses across 2 accounts."""
import requests, json, time, random, threading, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE = "http://127.0.0.1:8000"

# Load test data files
DATA_FILES = [
    "Saramsa-Data/Data-30.json",
    "Saramsa-Data/Data-50.json",
    "Saramsa-Data/Data-100.json",
    "Saramsa-Data/Data-200.json",
]

comments_pool = []
for f in DATA_FILES:
    with open(f) as fh:
        comments_pool.append((f, json.load(fh)))

# Login both users
def login(email, password):
    r = requests.post(f"{BASE}/api/auth/login/", json={"email": email, "password": password})
    d = r.json()
    return d["data"]["access"], d["data"]["user"]["id"]

print("Logging in...")
token1, uid1 = login("rakeshmahendran99@gmail.com", "R@kesh99")
token2, uid2 = login("testuser2@saramsa.com", "T@stUser2")

PROJECT1 = "11d1d1ff-ec5a-4c7f-8b87-7a04d16a4c09"
PROJECT2 = "c215dd9d-76ef-44b9-a1d7-558b00b49e9f"

accounts = [
    {"token": token1, "uid": uid1, "project": PROJECT1, "label": "User1"},
    {"token": token2, "uid": uid2, "project": PROJECT2, "label": "User2"},
]

# Build 25 tasks: mix of accounts and data sizes
tasks_to_run = []
for i in range(25):
    acct = accounts[i % 2]
    fname, comments = random.choice(comments_pool)
    # Take a random subset to vary sizes
    subset_size = random.randint(5, min(30, len(comments)))
    subset = random.sample(comments, subset_size)
    tasks_to_run.append({
        "idx": i + 1,
        "account": acct,
        "comments": subset,
        "data_file": fname,
        "comment_count": len(subset),
    })

print(f"\n{'='*70}")
print(f"  LOAD TEST: {len(tasks_to_run)} concurrent analyses across 2 accounts")
print(f"{'='*70}")
for t in tasks_to_run:
    print(f"  Task {t['idx']:2d}: {t['account']['label']} | {t['comment_count']:3d} comments | {t['data_file']}")
print(f"{'='*70}\n")

# Dispatch all analyses
def dispatch(task):
    acct = task["account"]
    headers = {"Authorization": f"Bearer {acct['token']}", "Content-Type": "application/json"}
    payload = {"project_id": acct["project"], "comments": task["comments"]}
    start = time.time()
    r = requests.post(f"{BASE}/api/insights/analyze/", json=payload, headers=headers)
    elapsed = time.time() - start
    if r.status_code in (200, 202):
        data = r.json()["data"]
        return {**task, "task_id": data["task_id"], "analysis_id": data["analysis_id"],
                "dispatch_time": elapsed, "status": "dispatched"}
    else:
        return {**task, "task_id": None, "dispatch_time": elapsed,
                "status": f"DISPATCH_FAILED({r.status_code})", "error": r.text[:200]}

print("Dispatching all tasks concurrently...")
global_start = time.time()

with ThreadPoolExecutor(max_workers=25) as pool:
    futures = {pool.submit(dispatch, t): t for t in tasks_to_run}
    dispatched = []
    for f in as_completed(futures):
        result = f.result()
        dispatched.append(result)
        sym = "OK" if result["status"] == "dispatched" else "FAIL"
        print(f"  {sym} Task {result['idx']:2d} dispatched in {result['dispatch_time']:.1f}s "
              f"({result['account']['label']}, {result['comment_count']} comments)")

dispatch_time = time.time() - global_start
ok_tasks = [t for t in dispatched if t["status"] == "dispatched"]
fail_tasks = [t for t in dispatched if t["status"] != "dispatched"]

print(f"\nDispatched {len(ok_tasks)}/{len(dispatched)} tasks in {dispatch_time:.1f}s")
if fail_tasks:
    print(f"FAILED dispatches:")
    for t in fail_tasks:
        print(f"  Task {t['idx']}: {t['status']} - {t.get('error','')[:100]}")

# Poll for completion
print(f"\nPolling for results (max 10 min)...")
pending = {t["task_id"]: t for t in ok_tasks}
completed = {}
poll_start = time.time()
max_wait = 600  # 10 min

while pending and (time.time() - poll_start) < max_wait:
    time.sleep(3)
    for task_id in list(pending.keys()):
        t = pending[task_id]
        acct = t["account"]
        headers = {"Authorization": f"Bearer {acct['token']}"}
        try:
            r = requests.get(f"{BASE}/api/insights/task-status/{task_id}/", headers=headers, timeout=10)
            d = r.json()["data"]
            status = d["status"]
            if status not in ("RUNNING", "PENDING", "STARTED"):
                t["final_status"] = status
                t["final_data"] = d
                t["total_time"] = time.time() - global_start
                if d.get("result"):
                    t["processing_time"] = d["result"].get("processing_time", 0)
                    t["method"] = d["result"].get("processing_method", "?")
                else:
                    t["processing_time"] = 0
                    t["method"] = "?"
                    t["error"] = d.get("error", "")
                completed[task_id] = t
                del pending[task_id]
                sym = "OK" if status == "SUCCESS" else "FAIL"
                print(f"  {sym} Task {t['idx']:2d}: {status} | {t['processing_time']:.1f}s processing | "
                      f"{t['total_time']:.0f}s wall | {t['account']['label']} | {t['comment_count']} comments")
        except Exception as e:
            pass
    
    elapsed = time.time() - poll_start
    if pending:
        print(f"    ... {len(pending)} still running ({elapsed:.0f}s elapsed)")

total_time = time.time() - global_start

# Summary
print(f"\n{'='*70}")
print(f"  LOAD TEST RESULTS")
print(f"{'='*70}")
successes = [t for t in completed.values() if t["final_status"] == "SUCCESS"]
failures = [t for t in completed.values() if t["final_status"] != "SUCCESS"]
timeouts = list(pending.values())

print(f"  Total tasks:     {len(tasks_to_run)}")
print(f"  Succeeded:       {len(successes)}")
print(f"  Failed:          {len(failures)}")
print(f"  Timed out:       {len(timeouts)}")
print(f"  Dispatch time:   {dispatch_time:.1f}s")
print(f"  Total wall time: {total_time:.0f}s")

if successes:
    proc_times = [t["processing_time"] for t in successes]
    wall_times = [t["total_time"] for t in successes]
    print(f"\n  Processing time (per task):")
    print(f"    Min:    {min(proc_times):.1f}s")
    print(f"    Max:    {max(proc_times):.1f}s")
    print(f"    Avg:    {sum(proc_times)/len(proc_times):.1f}s")
    print(f"  Wall time (dispatch -> complete):")
    print(f"    First:  {min(wall_times):.0f}s")
    print(f"    Last:   {max(wall_times):.0f}s")
    
    # Per-user breakdown
    for label in ("User1", "User2"):
        user_tasks = [t for t in successes if t["account"]["label"] == label]
        if user_tasks:
            pt = [t["processing_time"] for t in user_tasks]
            print(f"\n  {label}: {len(user_tasks)} tasks, avg {sum(pt)/len(pt):.1f}s processing")

if failures:
    print(f"\n  Failed tasks:")
    for t in failures:
        print(f"    Task {t['idx']}: {t['final_status']} - {t.get('error','')[:100]}")

if timeouts:
    print(f"\n  Timed-out tasks:")
    for t in timeouts:
        print(f"    Task {t['idx']}: still pending after {max_wait}s")

print(f"{'='*70}")

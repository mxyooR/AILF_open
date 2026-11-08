"""Offline lifecycle, isolation, expiry and overload checks; no model or service I/O."""
import asyncio
import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("command_runtime_tested", Path(__file__).resolve().parents[2] / "app" / "core" / "command_runtime.py")
runtime_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_module)
CommandRuntime = runtime_module.CommandRuntime
TaskStateStore = runtime_module.TaskStateStore


class FakeRedis:
    def __init__(self):
        self.records = {}
        self.calls = 0
        self.fail = False

    async def setex(self, key, ttl, value):
        self.calls += 1
        if self.fail:
            raise ConnectionError("test backend offline")
        self.records[key] = value

    async def get(self, key):
        self.calls += 1
        if self.fail:
            raise ConnectionError("test backend offline")
        return self.records.get(key)

    async def aclose(self):
        pass


class CommandRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.runtimes = []

    async def asyncTearDown(self):
        for runtime in self.runtimes:
            await runtime.shutdown()

    def create(self, handler, store=None, **limits):
        runtime = CommandRuntime(handler, store or TaskStateStore(), **limits)
        self.runtimes.append(runtime)
        return runtime

    async def completed(self, runtime, ticket):
        for attempt in range(200):
            state = await runtime.get(ticket["task_id"], ticket["poll_token"])
            if state and state["status"] in {"SUCCESS", "FAILURE"}:
                return state
            await asyncio.sleep(0)
        self.fail("Task did not reach a terminal state")

    async def test_results_require_the_exact_task_credential(self):
        async def handler(**kwargs):
            return {"schema": {"type": "page"}}
        runtime = self.create(handler)
        first = await runtime.submit("first")
        second = await runtime.submit("second")
        self.assertIsNone(await runtime.get(first["task_id"], ""))
        self.assertIsNone(await runtime.get(first["task_id"], second["poll_token"]))
        result = await self.completed(runtime, first)
        self.assertEqual(result["result"]["schema"]["type"], "page")
        self.assertNotIn("_poll_digest", result)

    async def test_query_credentials_are_hashed_in_shared_storage(self):
        backend = FakeRedis()
        async def handler(**kwargs):
            return {}
        runtime = self.create(handler, TaskStateStore(backend))
        ticket = await runtime.submit("test")
        saved = backend.records["ai:command:task:" + ticket["task_id"]]
        self.assertNotIn(ticket["poll_token"], saved)
        self.assertIn("_poll_digest", json.loads(saved)["payload"])

    async def test_concurrency_and_outstanding_capacity_are_bounded(self):
        release = asyncio.Event()
        entered = asyncio.Event()
        active = 0
        maximum = 0
        async def handler(**kwargs):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            entered.set()
            await release.wait()
            active -= 1
            return {}
        runtime = self.create(handler, max_concurrent=1, max_pending=2)
        first = await runtime.submit("first")
        await entered.wait()
        second = await runtime.submit("second")
        with self.assertRaises(runtime_module.CommandCapacityError):
            await runtime.submit("overflow")
        await asyncio.sleep(0)
        self.assertEqual((await runtime.get(second["task_id"], second["poll_token"]))["status"], "PENDING")
        release.set()
        await self.completed(runtime, first)
        await self.completed(runtime, second)
        self.assertEqual(maximum, 1)

    async def test_execution_and_queue_wait_have_a_deadline(self):
        async def handler(**kwargs):
            await asyncio.Event().wait()
        runtime = self.create(handler, max_concurrent=1, max_pending=2, timeout=0.01)
        first = await runtime.submit("running")
        second = await runtime.submit("queued")
        await asyncio.sleep(0.04)
        for ticket in [first, second]:
            state = await runtime.get(ticket["task_id"], ticket["poll_token"])
            self.assertEqual(state["status"], "FAILURE")
            self.assertIn("超时", state["error"])

    async def test_failure_details_are_not_exposed_to_polling_clients(self):
        async def handler(**kwargs):
            raise ValueError("sensitive local diagnostics")
        runtime = self.create(handler)
        state = await self.completed(runtime, await runtime.submit("test"))
        self.assertEqual(state["status"], "FAILURE")
        self.assertNotIn("sensitive", state["error"])

    async def test_submission_takes_a_snapshot_of_context(self):
        async def handler(command, context):
            return context
        runtime = self.create(handler)
        context = {"nested": {"value": 1}}
        ticket = await runtime.submit("test", context)
        context["nested"]["value"] = 2
        state = await self.completed(runtime, ticket)
        self.assertEqual(state["result"]["nested"]["value"], 1)
        self.assertEqual(state["result"]["_inference_trace_id"], ticket["task_id"])

    async def test_shutdown_finishes_tasks_cancelled_before_they_start(self):
        async def handler(**kwargs):
            await asyncio.Event().wait()
        runtime = self.create(handler)
        ticket = await runtime.submit("test")
        await runtime.shutdown()
        state = await runtime.get(ticket["task_id"], ticket["poll_token"])
        self.assertEqual(state["status"], "FAILURE")
        with self.assertRaises(runtime_module.CommandRuntimeClosed):
            await runtime.submit("after shutdown")

    async def test_shared_results_can_be_read_from_another_runtime(self):
        backend = FakeRedis()
        async def handler(**kwargs):
            return {"ok": True}
        first = self.create(handler, TaskStateStore(backend))
        second = self.create(handler, TaskStateStore(backend))
        ticket = await first.submit("test")
        await self.completed(first, ticket)
        state = await second.get(ticket["task_id"], ticket["poll_token"])
        self.assertEqual(state["result"], {"ok": True})

    async def test_polling_does_not_extend_cache_or_shared_expiry(self):
        now = [1000.0]
        store = TaskStateStore(FakeRedis(), ttl=10, clock=lambda: now[0])
        await store.save("task", {"status": "SUCCESS"})
        now[0] += 9
        self.assertIsNotNone(await store.load("task"))
        now[0] += 2
        self.assertIsNone(await store.load("task"))
        self.assertNotIn("task", store._memory)

    async def test_cache_capacity_evicts_completed_results_before_active_jobs(self):
        store = TaskStateStore(max_entries=2)
        await store.save("active", {"status": "STARTED"})
        await store.save("old-result", {"status": "SUCCESS"})
        await store.save("new-result", {"status": "SUCCESS"})
        self.assertIsNotNone(await store.load("active"))
        self.assertIsNone(await store.load("old-result"))
        self.assertEqual(len(store._memory), 2)

    async def test_slow_redis_read_cannot_overwrite_a_newer_local_result(self):
        started, release = asyncio.Event(), asyncio.Event()
        class SlowRedis(FakeRedis):
            async def get(self, key):
                snapshot = self.records.get(key)
                started.set()
                await release.wait()
                return snapshot
        now = [1000.0]
        store = TaskStateStore(SlowRedis(), clock=lambda: now[0])
        await store.save("task", {"status": "STARTED"})
        polling = asyncio.create_task(store.load("task"))
        await started.wait()
        now[0] += 1
        await store.save("task", {"status": "SUCCESS", "result": {"ok": True}})
        release.set()
        self.assertEqual((await polling)["status"], "SUCCESS")
        self.assertEqual((await store.load("task"))["result"], {"ok": True})

    async def test_redis_outage_uses_local_state_with_a_retry_cooldown(self):
        now = [1000.0]
        backend = FakeRedis()
        backend.fail = True
        store = TaskStateStore(backend, clock=lambda: now[0])
        await store.save("task", {"status": "PENDING"})
        self.assertEqual((await store.load("task"))["status"], "PENDING")
        self.assertEqual(backend.calls, 1)
        now[0] += 11
        self.assertEqual((await store.load("task"))["status"], "PENDING")
        self.assertEqual(backend.calls, 2)

    async def test_invalid_limits_are_rejected(self):
        async def handler(**kwargs):
            return {}
        with self.assertRaises(ValueError):
            CommandRuntime(handler, TaskStateStore(ttl=10), timeout=10)
        with self.assertRaises(ValueError):
            CommandRuntime(handler, TaskStateStore(), max_concurrent=3, max_pending=2)

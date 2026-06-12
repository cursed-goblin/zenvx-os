#!/usr/bin/env python3
"""agent_integrated.py - ZenvX autonomous local AI agent (ReAct loop).

This is the main entrypoint started by zenvx-agent.service and the `zenvx`
command. It wires together the inference, tools, and monitoring packages into
a single ReAct (Reason -> Act -> Observe) loop that runs entirely on the local
machine.
"""
import json
import os
import sys
import time

from inference.llm_engine import LLMEngine
from inference.memory_manager import MemoryManager
from inference.conversation_manager import ConversationManager
from inference.cache_manager import CacheManager
from inference.error_recovery import ErrorRecovery
from inference.persistence import Persistence
from inference.undo_manager import UndoManager
from inference.sensory_pipeline import SensoryPipeline

from tools.executor import SafeExecutor
from tools.permission_handler import (
    PermissionHandler, SCREEN_CAPTURE, COMMAND_EXECUTION,
    WEB_SEARCH, PAYMENT_TRANSACTION,
)
from tools.logger import AuditLogger
from tools.web_search import WebSearch
from tools.request_limiter import RequestLimiter
from tools.payment_handler import PaymentHandler

from monitoring.integration import MonitoringIntegration

CONFIG_PATH = "/etc/zenvx/config.json"
MAX_ITERATIONS = 5

CYAN = "\033[38;2;0;255;204m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

SYSTEM_PROMPT = """You are ZenvX, a private local AI agent running entirely on \
the user's machine. You reason step-by-step and may use tools.

Reply with ONLY a single JSON object of the form:
{"thought": "<your reasoning>", "action": "<one action>", \
"parameters": {<key: value>}, "confidence": <0.0-1.0>}

Valid actions:
  search          parameters: {"query": str}        - web search
  execute         parameters: {"command": str}      - run a shell command
  recall          parameters: {"query": str}        - search your memory
  analyze_screen  parameters: {}                    - capture & describe screen
  payment_info    parameters: {"vendor": str, "product": str, \
"amount": number, "upi_id": str}
  respond         parameters: {"text": str}         - answer the user
  done            parameters: {"text": str}         - finish the task

Use 'respond' or 'done' when you have the answer. Never invent tool output.
"""


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"models": {}, "hardware": {}, "performance": {},
                "permissions": {}, "payment": {}}


class ZenvXAgent:
    def __init__(self, config):
        self.config = config
        self.llm = LLMEngine(config)
        self.memory = MemoryManager(config, llm=self.llm)
        self.conversations = ConversationManager()
        self.cache = CacheManager(
            default_ttl=config.get("permissions", {}).get("cache_ttl_seconds",
                                                          300))
        self.recovery = ErrorRecovery()
        self.persistence = Persistence()
        self.undo = UndoManager()
        self.sensory = SensoryPipeline(config)
        self.executor = SafeExecutor()
        self.permissions = PermissionHandler(
            config,
            cache_seconds=config.get("permissions", {}).get(
                "cache_ttl_seconds", 300))
        self.audit = AuditLogger()
        self.web = WebSearch()
        self.limiter = RequestLimiter(rate=1.0, burst=5)
        self.payments = PaymentHandler()
        self.monitor = MonitoringIntegration(config)

    # --- prompt construction -------------------------------------------
    def build_prompt(self, user_input, scratchpad):
        context = self.memory.context()
        parts = [SYSTEM_PROMPT]
        if context:
            parts.append("Conversation so far:\n" + context)
        parts.append("User: " + user_input)
        if scratchpad:
            parts.append("Previous steps this turn:\n" + scratchpad)
        parts.append("Respond with one JSON object:")
        return "\n\n".join(parts)

    @staticmethod
    def parse_decision(raw):
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return {"thought": "unparseable", "action": "respond",
                    "parameters": {"text": raw.strip()}, "confidence": 0.3}
        try:
            return json.loads(raw[start:end + 1])
        except ValueError:
            return {"thought": "json error", "action": "respond",
                    "parameters": {"text": raw[start:end + 1]},
                    "confidence": 0.3}

    # --- tool dispatch -------------------------------------------------
    def dispatch(self, action, params):
        if action == "search":
            if not self.permissions.request(
                    WEB_SEARCH, "Search the web", params.get("query", "")):
                return "Permission denied for web search."
            self.limiter.acquire("web")
            query = params.get("query", "")
            cached = self.cache.get("search:" + query)
            if cached:
                return cached
            result = self.recovery.execute_with_retry(
                self.web.search, query, key="web",
                fallback=lambda q: f"Search unavailable for: {q}")
            self.cache.set("search:" + query, result)
            return result

        if action == "execute":
            command = params.get("command", "")
            if not self.permissions.request(
                    COMMAND_EXECUTION, "Run a shell command", command):
                return "Permission denied for command execution."
            out = self.executor.run(command)
            return (out["stdout"] or out["stderr"]).strip()

        if action == "recall":
            return self.memory.recall(params.get("query", ""))

        if action == "analyze_screen":
            if not self.permissions.request(
                    SCREEN_CAPTURE, "Capture and analyze the screen"):
                return "Permission denied for screen capture."
            shot = self.sensory.capture_screen()
            if "path" in shot:
                return self.sensory.describe_image(shot["path"])
            return shot.get("error", "screen capture failed")

        if action == "payment_info":
            if not self.permissions.request(
                    PAYMENT_TRANSACTION, "Show payment instructions", params):
                return "Permission denied for payment information."
            info = self.payments.show_instructions(
                params.get("vendor", ""), params.get("product", ""),
                params.get("amount", 0), params.get("upi_id", ""))
            self.payments.record(
                params.get("vendor", ""), params.get("product", ""),
                params.get("amount", 0), params.get("upi_id", ""))
            return info

        return f"Unknown action: {action}"

    # --- main ReAct loop ----------------------------------------------
    def handle(self, user_input):
        scratchpad = ""
        final = ""
        last_thought = last_action = ""
        for i in range(MAX_ITERATIONS):
            prompt = self.build_prompt(user_input, scratchpad)
            start = time.time()
            raw = self.recovery.execute_with_retry(
                self.llm.generate, prompt, key="llm",
                fallback=lambda _p: '{"action": "respond", "parameters": '
                                    '{"text": "I could not process that."}, '
                                    '"confidence": 0.2, "thought": "fallback"}')
            latency = time.time() - start
            self.monitor.record(getattr(self.llm, "last_tps", 0.0), latency)

            decision = self.parse_decision(raw)
            thought = decision.get("thought", "")
            action = decision.get("action", "respond")
            params = decision.get("parameters", {})
            confidence = decision.get("confidence", 0.0)
            last_thought, last_action = thought, action

            print(f"{DIM}  [thought] {thought}{RESET}")
            print(f"{CYAN}  [action] {action}{RESET}")

            if action in ("respond", "done"):
                final = params.get("text", "")
                self.audit.log(action, thought, params, confidence, final, True)
                break

            observation = self.dispatch(action, params)
            self.audit.log(action, thought, params, confidence,
                           observation, True)
            scratchpad += (f"\nStep {i + 1}: action={action} "
                           f"observation={observation[:400]}")
            self.memory.add(f"[{action}] {observation[:400]}")
        else:
            final = "I reached the step limit before finishing. Here is what " \
                    "I found:\n" + scratchpad[-600:]

        self.memory.add("User: " + user_input)
        self.memory.add("ZenvX: " + final)
        self.conversations.add_turn(user_input, last_thought, last_action,
                                    scratchpad, final)
        self.persistence.save({"conversation_id":
                               self.conversations.conversation_id})
        return final

    def repl(self):
        print(f"{CYAN}{BOLD}ZenvX agent ready.{RESET} "
              f"{DIM}Type 'exit' to quit, 'undo' to revert.{RESET}")
        while True:
            try:
                user_input = input(f"\n{CYAN}\u25b6{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye.")
                return
            if user_input.lower() == "undo":
                print(self.undo.undo())
                continue
            answer = self.handle(user_input)
            print(f"\n{BOLD}{answer}{RESET}")


def main():
    config = load_config()
    agent = ZenvXAgent(config)
    if len(sys.argv) > 1:
        # one-shot mode: zenvx "do this thing"
        print(agent.handle(" ".join(sys.argv[1:])))
    else:
        agent.repl()


if __name__ == "__main__":
    main()

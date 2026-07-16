"""Qwen-VL computer-use agent adapted for :class:`web_env.env.WebEnv`.

Based on the OSWorld-V2 ``mm_agents/qwen35vl_agent.py`` pattern:

- OpenAI-compatible chat API (LiteLLM / vLLM / etc.)
- XML ``<tool_call>`` computer-use tool format
- History truncation + screenshot folding

Differences from the OSWorld desktop agent:

- Prompts describe a **web browser** over CUA-Gym mock websites, not a full
  Ubuntu desktop.
- Parsed tool calls become :mod:`web_env.actions` dicts (pixel-coordinate
  primary; optional ``selector`` supported) instead of ``pyautogui`` code
  strings, so they can be passed straight to ``WebEnv.step(action)``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import openai
from requests.exceptions import SSLError

from web_env.agents.image_utils import process_image

logger = logging.getLogger("web_env.agents.qwen_vl")

MAX_RETRY_TIMES = int(os.getenv("WEBENV_MAX_RETRY_TIMES", "5"))

# Model tool-call action names -> WebEnv action ``type`` values.
_ACTION_TYPE_MAP = {
    "left_click": "click",
    "click": "click",
    "right_click": "right_click",
    "double_click": "double_click",
    "type": "type",
    "key": "key",
    "scroll": "scroll",
    "drag": "drag",
    "left_click_drag": "drag",
    "hover": "hover",
    "mouse_move": "hover",
    "wait": "wait",
    "terminate": "terminate",
}


def _format_prompt_date(value: Any = None) -> str:
    if value is None:
        return datetime.today().strftime("%A, %B %d, %Y")
    if isinstance(value, datetime):
        return value.strftime("%A, %B %d, %Y")
    if isinstance(value, date):
        return value.strftime("%A, %B %d, %Y")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return datetime.today().strftime("%A, %B %d, %Y")
        try:
            return datetime.fromisoformat(text).strftime("%A, %B %d, %Y")
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).strftime("%A, %B %d, %Y")
            except ValueError:
                pass
        return text
    return str(value)


class QwenVLAgent:
    """Lightweight vision-language agent for WebEnv rollouts.

    Call :meth:`reset` at the start of each episode, then :meth:`predict`
    once per step with the current observation. Returns
    ``(raw_response, [web_env_action_dict, ...])``.
    """

    COLLAPSED_SCREENSHOT_TEXT = "This screenshot has been collapsed."

    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        temperature: float = 0.0,
        history_n: int = 100,
        coordinate_type: str = "absolute",
        image_max: int = 20,
        fold_size: int = 10,
        collapse_text: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        message_cache_dir: Optional[str] = None,
    ):
        self.model = model or os.getenv("WEBENV_MODEL", "qwen3_5_yiding")
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.temperature = temperature
        self.history_n = history_n
        self.coordinate_type = coordinate_type
        self.image_max = int(image_max)
        self.fold_size = int(fold_size)
        self.collapse_text = collapse_text or self.COLLAPSED_SCREENSHOT_TEXT
        self.base_url = base_url or os.getenv(
            "WEBENV_BASE_URL",
            os.getenv("OPENAI_BASE_URL", "http://litellm.tiktok-row.net/v1"),
        )
        self.api_key = api_key or os.getenv(
            "WEBENV_API_KEY",
            os.getenv("OPENAI_API_KEY", "sk-1234"),
        )
        self.timeout = timeout or float(os.getenv("WEBENV_OPENAI_TIMEOUT", "180"))
        self.message_cache_dir = message_cache_dir

        if self.coordinate_type not in {"absolute", "relative"}:
            raise ValueError("coordinate_type must be 'absolute' or 'relative'")
        if self.image_max < 1:
            raise ValueError("image_max must be >= 1")
        if self.fold_size < 1:
            raise ValueError("fold_size must be >= 1")

        self.actions: List[str] = []
        self.responses: List[str] = []
        self.screenshots: List[str] = []
        self.folded_prefix_k = 0
        self.task_current_date = None

    # --- folding helpers -------------------------------------------------

    def _update_folding_state(self, total_screenshots: int) -> None:
        while (total_screenshots - self.folded_prefix_k) > self.image_max:
            self.folded_prefix_k += self.fold_size
        if self.folded_prefix_k > total_screenshots:
            self.folded_prefix_k = total_screenshots

    def _should_collapse_step(self, step_num_1based: int) -> bool:
        return step_num_1based <= self.folded_prefix_k

    def _wrap_tool_response(self, parts: List[Dict]) -> List[Dict]:
        return (
            [{"type": "text", "text": "<tool_response>\n"}]
            + parts
            + [{"type": "text", "text": "\n</tool_response>"}]
        )

    @staticmethod
    def _sanitize_messages_for_dump(messages: List[Dict]) -> List[Dict]:
        sanitized: List[Dict] = []
        for message in messages:
            cloned = {"role": message.get("role"), "content": []}
            for part in message.get("content", []) or []:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    url = ((part.get("image_url") or {}).get("url")) or ""
                    if url.startswith("data:image/"):
                        cloned["content"].append(
                            {
                                "type": "image_url",
                                "image_url": {"url": url[:40] + "...<omitted>"},
                            }
                        )
                    else:
                        cloned["content"].append(part)
                else:
                    cloned["content"].append(part)
            sanitized.append(cloned)
        return sanitized

    # --- prompt builders -------------------------------------------------

    def _build_tools_def(self, processed_width: int, processed_height: int) -> dict:
        if self.coordinate_type == "absolute":
            res_line = f"* The browser viewport resolution is {processed_width}x{processed_height}."
        else:
            res_line = "* The browser viewport resolution is 1000x1000 (normalized coordinates)."

        description_prompt = "\n".join(
            [
                "Use a mouse and keyboard to interact with a web browser showing a mock web application.",
                "* You are controlling a Chromium browser tab. Interact with the page UI via clicks, typing, scrolling, and keyboard shortcuts.",
                "* Some pages take time to update after an action; wait and look at the next screenshot before deciding the next move.",
                res_line,
                "* Before clicking, consult the screenshot to locate the target element's coordinates.",
                "* Click the center of buttons, links, and icons — not their edges.",
                "* Prefer interacting with the page UI over navigating away. Do not invent URLs unless the task explicitly asks you to.",
            ]
        )

        action_description_prompt = """
* `left_click`: Click the left mouse button at (x, y). Optional `text` holds modifier keys (e.g. "ctrl", "shift").
* `right_click`: Right-click at (x, y).
* `double_click`: Double-click at (x, y).
* `type`: Type a string of text. Prefer focusing an input (click it) first, then type.
* `key`: Press one or more keys in order (hotkeys). Pass `keys` as an array, e.g. ["Control", "a"].
* `scroll`: Scroll the mouse wheel. Positive `pixels` scrolls up; negative scrolls down. Optional `coordinate` sets the cursor position first.
* `left_click_drag`: Click-and-drag from the current cursor (or optional start) to `coordinate`.
* `hover` / `mouse_move`: Move the cursor to (x, y) without clicking.
* `wait`: Wait for the page to settle (pass `time` in seconds).
* `terminate`: End the task. Set `status` to "success" or "failure"."""

        return {
            "type": "function",
            "function": {
                "name": "computer_use",
                "description": description_prompt,
                "parameters": {
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": action_description_prompt,
                            "enum": [
                                "left_click",
                                "right_click",
                                "double_click",
                                "type",
                                "key",
                                "scroll",
                                "left_click_drag",
                                "hover",
                                "mouse_move",
                                "wait",
                                "terminate",
                            ],
                        },
                        "keys": {
                            "type": "array",
                            "description": "Required by `action=key`.",
                        },
                        "text": {
                            "type": "string",
                            "description": (
                                "Required by `action=type`. Optional for click/scroll "
                                "actions as modifier keys (e.g. 'ctrl', 'shift')."
                            ),
                        },
                        "coordinate": {
                            "type": "array",
                            "description": "(x, y) pixel coordinates on the screenshot.",
                        },
                        "pixels": {
                            "type": "number",
                            "description": "Scroll amount for `action=scroll`.",
                        },
                        "time": {
                            "type": "number",
                            "description": "Seconds to wait for `action=wait`.",
                        },
                        "status": {
                            "type": "string",
                            "description": "Task status for `action=terminate`.",
                            "enum": ["success", "failure"],
                        },
                    },
                },
            },
        }

    def _build_system_prompt(self, tools_def: dict) -> str:
        return (
            "You are a multi-purpose intelligent assistant controlling a web browser. "
            "Based on my requests, you can use tools to help me complete web UI tasks "
            "on mock websites.\n\n"
            "# Tools\n\n"
            "You have access to the following functions:\n\n"
            "<tools>\n"
            + json.dumps(tools_def, ensure_ascii=False)
            + "\n</tools>\n\n"
            "If you choose to call a function ONLY reply in the following format with NO suffix:\n\n"
            "<tool_call>\n"
            "<function=example_function_name>\n"
            "<parameter=example_parameter_1>\n"
            "value_1\n"
            "</parameter>\n"
            "<parameter=example_parameter_2>\n"
            "This is the value for the second parameter\n"
            "that can span\n"
            "multiple lines\n"
            "</parameter>\n"
            "</function>\n"
            "</tool_call>\n\n"
            "<IMPORTANT>\n"
            "Reminder:\n"
            "- Function calls MUST follow the specified format: an inner <function=...></function> "
            "block must be nested within <tool_call></tool_call> XML tags\n"
            "- Required parameters MUST be specified\n"
            "- You may provide optional reasoning for your function call in natural language "
            "BEFORE the function call, but NOT after\n"
            "- If there is no function call available, answer the question like normal with "
            "your current knowledge and do not tell the user about function calls\n"
            f"- The current date is {_format_prompt_date(self.task_current_date)}.\n"
            f"- Collapsed screenshots appear as text: {self.collapse_text}\n"
            "</IMPORTANT>\n\n"
            "# Response format\n\n"
            "Response format for every step:\n"
            "1) Action: a short imperative describing what to do in the UI.\n"
            "2) A single <tool_call>...</tool_call> block.\n\n"
            "Rules:\n"
            "- Output exactly in the order: Action, <tool_call>.\n"
            "- Be brief: one sentence for Action.\n"
            "- Do not output anything else outside those parts.\n"
            "- If finishing, use action=terminate in the tool call."
        )

    # --- predict ---------------------------------------------------------

    def predict(
        self, instruction: str, obs: Dict[str, Any]
    ) -> Tuple[str, List[dict]]:
        """Produce the next WebEnv action(s) for ``instruction`` given ``obs``.

        Args:
            instruction: natural-language task instruction.
            obs: WebEnv observation dict (must contain ``"screenshot"`` as
                ``np.ndarray`` or PNG bytes).

        Returns:
            ``(raw_model_response, list_of_web_env_action_dicts)``.
        """
        screenshot = obs["screenshot"]
        processed_b64, (orig_w, orig_h), (proc_w, proc_h) = process_image(screenshot)

        self.screenshots.append(processed_b64)
        total_steps = len(self.screenshots)
        self._update_folding_state(total_steps)

        start_step = max(1, total_steps - self.history_n)
        previous_actions = [
            f"Step {i + 1}: {self.actions[i]}"
            for i in range(0, min(start_step - 1, len(self.actions)))
        ]
        previous_actions_str = "\n".join(previous_actions) if previous_actions else "None"

        tools_def = self._build_tools_def(proc_w, proc_h)
        system_prompt = self._build_system_prompt(tools_def)
        instruction_prompt = (
            "\nPlease generate the next move according to the UI screenshot, "
            "instruction and previous actions.\n\n"
            f"Instruction: {instruction}\n\n"
            f"Previous actions:\n{previous_actions_str}"
        )

        messages: List[Dict] = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]}
        ]

        for step_num in range(start_step, total_steps + 1):
            is_first_turn = step_num == start_step
            is_collapsed = self._should_collapse_step(step_num)

            if is_collapsed:
                parts = [{"type": "text", "text": self.collapse_text}]
                if is_first_turn:
                    user_content = [{"type": "text", "text": instruction_prompt}]
                else:
                    user_content = self._wrap_tool_response(parts)
                messages.append({"role": "user", "content": user_content})
            else:
                img_url = f"data:image/png;base64,{self.screenshots[step_num - 1]}"
                if is_first_turn:
                    user_content = [
                        {"type": "image_url", "image_url": {"url": img_url}},
                        {"type": "text", "text": instruction_prompt},
                    ]
                else:
                    user_content = self._wrap_tool_response(
                        [{"type": "image_url", "image_url": {"url": img_url}}]
                    )
                messages.append({"role": "user", "content": user_content})

            if step_num <= total_steps - 1 and (step_num - 1) < len(self.responses):
                messages.append(
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": self.responses[step_num - 1]}],
                    }
                )

        self._maybe_dump_messages(messages, total_steps - 1)

        response = self.call_llm(
            {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "temperature": self.temperature,
            }
        )
        logger.info("QwenVL Output: %s", response)
        self.responses.append(response or "")

        low_level_instruction, actions = self.parse_response(
            response or "",
            original_width=orig_w,
            original_height=orig_h,
            processed_width=proc_w,
            processed_height=proc_h,
        )
        logger.info("Low level instruction: %s", low_level_instruction)
        logger.info("WebEnv actions: %s", actions)

        self.actions.append(low_level_instruction)
        return response or "", actions

    # --- parse XML tool calls -> WebEnv actions --------------------------

    def parse_response(
        self,
        response: str,
        original_width: Optional[int] = None,
        original_height: Optional[int] = None,
        processed_width: Optional[int] = None,
        processed_height: Optional[int] = None,
    ) -> Tuple[str, List[dict]]:
        low_level_instruction = ""
        actions: List[dict] = []

        if not response or not response.strip():
            return low_level_instruction, actions

        def adjust_coordinates(x: float, y: float) -> Tuple[int, int]:
            if not (original_width and original_height):
                return int(x), int(y)
            if self.coordinate_type == "absolute":
                if processed_width and processed_height:
                    return (
                        int(x * original_width / processed_width),
                        int(y * original_height / processed_height),
                    )
                return int(x), int(y)
            return (
                int(x * original_width / 999),
                int(y * original_height / 999),
            )

        def parse_xml_tool_call(xml_content: str) -> Optional[Dict]:
            params: Dict = {}
            func_match = re.search(r"<function=([^>]+)>", xml_content)
            if not func_match or func_match.group(1) != "computer_use":
                return None
            for match in re.finditer(
                r"<parameter=([^>]+)>\s*(.*?)\s*</parameter>", xml_content, re.DOTALL
            ):
                name = match.group(1)
                value = match.group(2).strip()
                if value.startswith("[") or value.startswith("{"):
                    try:
                        params[name] = json.loads(value)
                        continue
                    except json.JSONDecodeError:
                        pass
                params[name] = value
            return params

        def parse_keys(raw_keys) -> List[str]:
            if isinstance(raw_keys, str):
                try:
                    raw_keys = json.loads(raw_keys)
                except Exception:
                    raw_keys = [raw_keys]
            if isinstance(raw_keys, list):
                return [str(k).strip() for k in raw_keys]
            return [str(raw_keys).strip()]

        def parse_coordinate(raw_coord) -> Optional[Tuple[float, float]]:
            if isinstance(raw_coord, str):
                try:
                    raw_coord = json.loads(raw_coord)
                except Exception:
                    return None
            if isinstance(raw_coord, list) and len(raw_coord) >= 2:
                return float(raw_coord[0]), float(raw_coord[1])
            return None

        def process_tool_call_params(params: Dict) -> None:
            raw_action = params.get("action")
            if not raw_action:
                return
            action_type = _ACTION_TYPE_MAP.get(str(raw_action))
            if not action_type:
                logger.warning("Unknown tool action %r — skipped", raw_action)
                return

            coordinate = parse_coordinate(params.get("coordinate"))
            text = params.get("text")
            action: dict = {"type": action_type}

            if action_type in {"click", "right_click", "double_click", "hover"}:
                if coordinate:
                    x, y = adjust_coordinates(*coordinate)
                    action["x"], action["y"] = x, y
                else:
                    # Clicks without a coordinate are invalid for WebEnv pixel
                    # targeting — skip rather than invent (0,0).
                    if action_type != "hover":
                        logger.warning("%s without coordinate — skipped", action_type)
                        return
                    action["x"], action["y"] = 0, 0
                if text and action_type == "click":
                    # Modifier keys held during click → convert to a preceding
                    # key-down isn't supported by WebEnv; ignore for the base agent.
                    pass
                if action_type == "click":
                    action["button"] = "left"
            elif action_type == "type":
                action["text"] = "" if text is None else str(text)
            elif action_type == "key":
                keys = parse_keys(params.get("keys", []))
                action["keys"] = keys if len(keys) > 1 else (keys[0] if keys else "")
            elif action_type == "scroll":
                if coordinate:
                    x, y = adjust_coordinates(*coordinate)
                    action["x"], action["y"] = x, y
                try:
                    pixels = int(float(params.get("pixels", 0)))
                except (TypeError, ValueError):
                    pixels = 0
                # WebEnv scroll: positive dy scrolls down in Playwright's mouse.wheel.
                # OSWorld pyautogui.scroll(positive) scrolls up — flip the sign so
                # model intent ("scroll down to see more") matches Playwright.
                action["dy"] = -pixels
                action["dx"] = 0
            elif action_type == "drag":
                if not coordinate:
                    logger.warning("drag without destination coordinate — skipped")
                    return
                to_x, to_y = adjust_coordinates(*coordinate)
                action["to_x"], action["to_y"] = to_x, to_y
                # Without an explicit start, drag from a small offset so WebEnv
                # validation (requires x/y or selector) is satisfied. Prefer
                # hovering to the start first in a prior step when possible.
                action["x"] = action.get("x", max(to_x - 50, 0))
                action["y"] = action.get("y", to_y)
            elif action_type == "wait":
                try:
                    seconds = float(params.get("time", 1.0))
                except (TypeError, ValueError):
                    seconds = 1.0
                action["ms"] = int(seconds * 1000)
            elif action_type == "terminate":
                action["status"] = params.get("status", "success")

            actions.append(action)

        for line in response.split("\n"):
            stripped = line.strip()
            if stripped.lower().startswith("action:"):
                low_level_instruction = stripped.split(":", 1)[-1].strip()
                break

        for tool_call_match in re.finditer(
            r"<tool_call>(.*?)</tool_call>", response, re.DOTALL
        ):
            params = parse_xml_tool_call(tool_call_match.group(1))
            if params:
                process_tool_call_params(params)

        if not low_level_instruction and actions:
            first = actions[0]
            if first.get("type") == "terminate":
                low_level_instruction = "Task completed"
            elif first.get("type") == "wait":
                low_level_instruction = "Waiting"
            else:
                low_level_instruction = f"Performing {first.get('type')} action"

        return low_level_instruction, actions

    # --- LLM call --------------------------------------------------------

    @staticmethod
    def _extract_content_text(content) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part.get("text", ""))
                else:
                    text = getattr(part, "text", None)
                    if text:
                        parts.append(text)
            return "".join(parts)
        return str(content)

    def call_llm(self, payload: Dict) -> str:
        try:
            client = openai.OpenAI(
                base_url=self.base_url, api_key=self.api_key, timeout=self.timeout
            )
        except TypeError:
            client = openai.OpenAI(base_url=self.base_url, api_key=self.api_key)

        retryable_types = tuple(
            exc
            for exc in [
                SSLError,
                getattr(openai, "APIConnectionError", None),
                getattr(openai, "APITimeoutError", None),
                getattr(openai, "RateLimitError", None),
                getattr(openai, "BadRequestError", None),
                getattr(openai, "InternalServerError", None),
            ]
            if isinstance(exc, type)
        )

        last_err: Optional[Exception] = None
        for attempt in range(1, MAX_RETRY_TIMES + 1):
            try:
                response = client.chat.completions.create(
                    model=payload.get("model", self.model),
                    messages=payload["messages"],
                    max_tokens=payload.get("max_tokens", self.max_tokens),
                    temperature=payload.get("temperature", self.temperature),
                    top_p=payload.get("top_p", self.top_p),
                )
                return self._extract_content_text(response.choices[0].message.content)
            except retryable_types as exc:
                last_err = exc
                logger.warning(
                    "call_llm failed attempt %d/%d: %s", attempt, MAX_RETRY_TIMES, exc
                )
                time.sleep(min(5.0 * attempt, 30.0))

        if last_err is not None:
            raise last_err
        return ""

    def _maybe_dump_messages(self, messages: List[Dict], step_idx: int) -> None:
        if not self.message_cache_dir:
            return
        try:
            os.makedirs(self.message_cache_dir, exist_ok=True)
            path = os.path.join(
                self.message_cache_dir, f"qwen_vl_messages_step_{step_idx}.json"
            )
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    self._sanitize_messages_for_dump(messages),
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to dump debug messages: %s", exc)

    def reset(self, _logger: Optional[logging.Logger] = None) -> None:
        """Clear per-episode history. Call once before each new task."""
        global logger
        if _logger is not None:
            logger = _logger
        self.actions = []
        self.responses = []
        self.screenshots = []
        self.folded_prefix_k = 0

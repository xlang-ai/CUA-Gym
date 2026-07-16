"""Example WebTask: book and pay for a train ticket on the 12306 mock.

Grounded in ``hub/websites/12306_mock/SCHEMA.md``:

- Submitting a booking (提交订单) appends an order to ``orders`` with
  ``status == "待支付"``.
- Confirming payment (确认支付) flips that order's ``status`` to
  ``"已支付"`` and sets ``paidAt``.

This is the reference implementation for how a :class:`~web_env.task.WebTask`
should be written against a CUA-Gym-Hub mock: seed a minimal, schema-valid
``initial_state()``, then award partial credit per sub-goal in ``evaluate()``
by reading the live ``current_state.orders`` from the mock's ``/go`` endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from web_env.task import WebTask

if TYPE_CHECKING:
    from web_env.env import WebEnv

TARGET_TRAIN_NO = "G7"
TARGET_SEAT_CLASS = "secondClassSeat"
TARGET_PASSENGER_NAME = "张伟"


class Book12306Task(WebTask):
    """Book a 2nd-class ticket on train G7 (北京南→上海虹桥) and pay for it."""

    task_id = "12306_book_pay"
    mock = "12306_mock"
    instruction = (
        "You are logged in to 12306 as 张伟. Search for and book a second-class "
        "seat (二等座) on train G7 from 北京南 to 上海虹桥 for yourself, then "
        "confirm payment for the order."
    )

    def initial_state(self) -> dict:
        # Only the top-level keys this task actually depends on are
        # overridden; per SCHEMA.md, omitting `stations`/`trains` falls back
        # to the mock's built-in default seed data (which includes G7 on the
        # 北京南→上海虹桥 route), so we don't need to fabricate train data here.
        return {
            "user": {
                "id": "user_001",
                "name": "张伟",
                "username": "zhangwei2024",
                "idType": "身份证",
                "idNumber": "110101199001011234",
                "phone": "138****5678",
                "email": "zhangwei@example.com",
                "memberLevel": "普通会员",
                "memberPoints": 2680,
            },
            "passengers": [
                {
                    "id": "psg_001",
                    "name": "张伟",
                    "idType": "身份证",
                    "idNumber": "110101199001011234",
                    "phone": "13812345678",
                    "passengerType": "成人",
                    "isDefault": True,
                    "seatPreference": "窗口",
                }
            ],
            "orders": [],
            "waitlistOrders": [],
            "searchHistory": [],
            "notifications": [],
            "currentSearch": {
                "from": "北京",
                "to": "上海",
                "date": "2026-04-15",
                "isStudent": False,
                "isHighSpeedOnly": False,
                "tripType": "oneWay",
                "returnDate": None,
            },
            "selectedTrain": None,
            "selectedSeatClass": None,
            "selectedPassengers": [],
            "searchFilters": {
                "timeRanges": [],
                "trainTypes": [],
                "sortBy": "departureTime",
                "sortDir": "asc",
            },
        }

    def evaluate(self, env: "WebEnv", go: dict) -> float:
        current = self.current_state(go)
        orders = current.get("orders", [])

        booked_order = None
        for order in orders:
            if order.get("trainNo") != TARGET_TRAIN_NO:
                continue
            if order.get("seatClass") != TARGET_SEAT_CLASS:
                continue
            passenger_names = {p.get("name") for p in order.get("passengers", [])}
            if TARGET_PASSENGER_NAME in passenger_names:
                booked_order = order
                break

        score = 0.0
        if booked_order is not None:
            # Sub-goal 1: order created (booking submitted).
            score += 0.5
            # Sub-goal 2: order paid.
            if booked_order.get("status") == "已支付" and booked_order.get("paidAt"):
                score += 0.5

        return self._clamp01(score)


TASK_CLASS = Book12306Task

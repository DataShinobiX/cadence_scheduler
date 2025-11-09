from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base import BaseAgent


API_KEY = "sk-aU7KLAifP85EWxg4J7NFJg"
BASE_URL = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
MODEL = "gpt-4.1-mini"


@dataclass
class DayEvent:
    """Normalized representation of a scheduled block."""

    source: str
    description: str
    start: datetime
    end: datetime
    duration_minutes: int

    @property
    def date(self) -> date:
        return self.start.date()


class MealRecommendationAgent(BaseAgent):
    """
    Agent 4: Meal Recommendation Advisor

    Examines the user's schedule for the earliest upcoming day and suggests
    whether to gently recommend ordering lunch or dinner.
    """

    def __init__(self) -> None:
        super().__init__(name="MealRecommendationAgent")
        self.temperature = 0.2
        try:
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(
                model=MODEL,
                api_key=API_KEY,
                base_url=BASE_URL,
                temperature=self.temperature,
            )
            print("[MEAL AGENT] ✅ Initialized LLM client")
        except Exception as exc:  # pragma: no cover - best effort logging
            print(f"[MEAL AGENT] ⚠️ Unable to initialize LLM client: {exc}")
            self.llm = None

    # ------------------------------------------------------------------ PUBLIC
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("\n[MEAL AGENT] 🍽️ Evaluating meal recommendation opportunities...")

        try:
            timeline = self._build_day_timeline(state)
        except Exception as exc:
            print(f"[MEAL AGENT] ❌ Failed to build timeline: {exc}")
            timeline = None

        if not timeline:
            print("[MEAL AGENT] ℹ️  No qualifying schedule found for recommendation analysis.")
            state["meal_recommendations"] = []
            return state

        payload = self._build_analysis_payload(timeline, state)
        recommendation: Optional[Dict[str, Any]] = None

        if self.llm:
            recommendation = self._invoke_llm(payload)

        if not recommendation:
            print("[MEAL AGENT] ⚠️ Falling back to heuristic recommendation.")
            recommendation = self._heuristic_recommendation(payload)

        if not recommendation or not recommendation.get("should_recommend"):
            print("[MEAL AGENT] ✅ No meal recommendation needed.")
            state["meal_recommendations"] = []
            return state

        structured = self._structure_recommendations(recommendation, payload)
        state["meal_recommendations"] = structured
        state["proactive_notifications"].extend(
            self._to_notifications(structured, payload)
        )

        print(f"[MEAL AGENT] ✅ Generated {len(structured)} recommendation(s).")
        for item in structured:
            print(
                f"  - ({item['meal'].title()}) {item['message']} "
                f"[confidence={item['confidence']}]"
            )

        state["current_agent"] = "Meal Recommendation Complete"
        return state

    # ----------------------------------------------------------------- HELPERS
    def _build_day_timeline(self, state: Dict[str, Any]) -> Optional[List[DayEvent]]:
        """Collect the earliest upcoming day's events from scheduling plan and calendar."""
        plan = state.get("scheduling_plan") or []
        existing = state.get("existing_calendar") or []

        events: List[DayEvent] = []

        for item in plan:
            start = self._parse_dt(item.get("start_time"))
            end = self._parse_dt(item.get("end_time"))
            if not start:
                continue
            if not end:
                duration = int(item.get("duration_minutes") or 60)
                end = start + timedelta(minutes=duration)
            duration_minutes = int(
                item.get("duration_minutes") or (end - start).total_seconds() // 60
            )
            events.append(
                DayEvent(
                    source="scheduled_plan",
                    description=(item.get("description") or "Task").strip(),
                    start=start,
                    end=end,
                    duration_minutes=max(duration_minutes, 15),
                )
            )

        for item in existing:
            start = self._parse_dt(
                item.get("start_datetime") or item.get("start_time")
            )
            end = self._parse_dt(item.get("end_datetime") or item.get("end_time"))
            if not start or not end:
                continue
            duration_minutes = int(
                (end - start).total_seconds() // 60 or item.get("duration_minutes") or 30
            )
            events.append(
                DayEvent(
                    source="existing_calendar",
                    description=(item.get("summary") or "Calendar event").strip(),
                    start=start,
                    end=end,
                    duration_minutes=max(duration_minutes, 5),
                )
            )

        if not events:
            return None

        # Sort by start time and pick earliest day
        events.sort(key=lambda ev: ev.start)
        earliest_day = events[0].date
        day_events = [event for event in events if event.date == earliest_day]

        if not day_events:
            return None

        print(
            f"[MEAL AGENT] 📅 Analyzing {len(day_events)} event(s) on "
            f"{earliest_day.isoformat()}"
        )
        return day_events

    def _build_analysis_payload(
        self, day_events: List[DayEvent], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create structured payload for the LLM and fallbacks."""
        meal_windows = {
            "lunch": {"start": "12:00", "end": "14:00"},
            "dinner": {"start": "18:00", "end": "20:30"},
        }

        preferences = state.get("user_preferences") or {}
        if "lunch_time_start" in preferences and "lunch_duration_minutes" in preferences:
            lunch_start = preferences["lunch_time_start"]
            lunch_end_dt = datetime.combine(
                day_events[0].date,
                time.fromisoformat(preferences["lunch_time_start"]),
            ) + timedelta(minutes=int(preferences["lunch_duration_minutes"]))
            meal_windows["lunch"] = {
                "start": lunch_start,
                "end": lunch_end_dt.time().isoformat(timespec="minutes"),
            }
        if preferences.get("dinner_time_start") and preferences.get(
            "dinner_duration_minutes"
        ):
            dinner_start = preferences["dinner_time_start"]
            dinner_end_dt = datetime.combine(
                day_events[0].date,
                time.fromisoformat(preferences["dinner_time_start"]),
            ) + timedelta(minutes=int(preferences["dinner_duration_minutes"]))
            meal_windows["dinner"] = {
                "start": dinner_start,
                "end": dinner_end_dt.time().isoformat(timespec="minutes"),
            }

        serialized_events = [
            {
                "source": event.source,
                "description": event.description,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "duration_minutes": event.duration_minutes,
            }
            for event in sorted(day_events, key=lambda ev: ev.start)
        ]

        payload = {
            "date": day_events[0].date.isoformat(),
            "weekday": day_events[0].start.strftime("%A"),
            "timezone": preferences.get("timezone") or "UTC",
            "events": serialized_events,
            "meal_windows": meal_windows,
            "conversation_history_count": len(state.get("conversation_history") or []),
        }
        return payload

    def _invoke_llm(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call the LLM and parse its JSON response."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
        except Exception as exc:  # pragma: no cover
            print(f"[MEAL AGENT] ⚠️ LangChain message classes unavailable: {exc}")
            return None

        system_prompt = (
            "You are a thoughtful wellness assistant that reviews daily schedules. "
            "Decide if the user should receive a gentle suggestion to order lunch or "
            "dinner so they do not miss a meal. Prefer short, warm language."
        )
        human_prompt = (
            "Analyze the following schedule and respond ONLY with JSON using this schema:\n"
            "{\n"
            '  "should_recommend": true | false,\n'
            '  "meal": "lunch" | "dinner" | "both" | "none",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "reasoning": "brief explanation",\n'
            '  "supporting_factors": ["string", ...],\n'
            '  "message": "soft recommendation under 160 characters"\n'
            "}\n\n"
            "Prefer to recommend a meal when the user has long blocks of meetings or tasks "
            "with limited breaks (≤30 minutes) during the typical meal window. If they are "
            "already free around the meal window, do not recommend. Keep the message supportive "
            "and avoid sounding pushy.\n\n"
            f"SCHEDULE CONTEXT:\n{json.dumps(payload, ensure_ascii=False)}"
        )

        try:
            response = self.llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
            )
            content = getattr(response, "content", "") if response else ""
            parsed = json.loads(content) if content else None
            if isinstance(parsed, dict):
                return parsed
            print("[MEAL AGENT] ⚠️ LLM response was not a JSON object.")
            return None
        except Exception as exc:
            print(f"[MEAL AGENT] ❌ LLM invocation failed: {exc}")
            return None

    def _heuristic_recommendation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback heuristic if LLM is unavailable."""
        events = [
            (
                datetime.fromisoformat(item["start"]),
                datetime.fromisoformat(item["end"]),
                item["description"],
            )
            for item in payload.get("events", [])
        ]

        if not events:
            return {"should_recommend": False, "meal": "none"}

        lunch_window = self._window_range(payload, "lunch")
        dinner_window = self._window_range(payload, "dinner")

        lunch_busy = self._busy_minutes_in_window(events, lunch_window)
        dinner_busy = self._busy_minutes_in_window(events, dinner_window)

        recommendations: Dict[str, Any] = {
            "should_recommend": False,
            "meal": "none",
        }

        if lunch_busy >= 75:
            recommendations.update(
                {
                    "should_recommend": True,
                    "meal": "lunch",
                    "confidence": 0.55,
                    "reasoning": "Schedule is largely occupied during the lunchtime window.",
                    "supporting_factors": [
                        f"Busy minutes during lunch window: {int(lunch_busy)}"
                    ],
                    "message": self._format_message(payload, "lunch"),
                }
            )

        if dinner_busy >= 90:
            if recommendations["should_recommend"] and recommendations["meal"] == "lunch":
                recommendations["meal"] = "both"
                recommendations["supporting_factors"].append(
                    f"Busy minutes during dinner window: {int(dinner_busy)}"
                )
                recommendations["message"] = self._format_message(payload, "both")
                recommendations["confidence"] = 0.6
            else:
                recommendations.update(
                    {
                        "should_recommend": True,
                        "meal": "dinner",
                        "confidence": 0.52,
                        "reasoning": "Evening is tightly booked around dinner time.",
                        "supporting_factors": [
                            f"Busy minutes during dinner window: {int(dinner_busy)}"
                        ],
                        "message": self._format_message(payload, "dinner"),
                    }
                )

        return recommendations

    def _structure_recommendations(
        self, data: Dict[str, Any], payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Expand combined responses into per-meal structures."""
        meal = data.get("meal", "none")
        meals = []
        if meal == "both":
            meals = ["lunch", "dinner"]
        elif meal in {"lunch", "dinner"}:
            meals = [meal]
        else:
            meals = []

        recommendations: List[Dict[str, Any]] = []
        for meal_name in meals:
            rec_id = f"meal-{payload['date']}-{meal_name}"
            recommendations.append(
                {
                    "id": rec_id,
                    "date": payload["date"],
                    "weekday": payload["weekday"],
                    "meal": meal_name,
                    "message": self._format_message(payload, meal_name, data),
                    "confidence": round(float(data.get("confidence", 0.5)), 2),
                    "reason": data.get("reasoning") or "Busy schedule around meal time.",
                    "supporting_factors": data.get("supporting_factors", []),
                    "generated_at": datetime.utcnow().isoformat(),
                    "generated_by": self.name,
                }
            )
        return recommendations

    def _to_notifications(
        self, recommendations: List[Dict[str, Any]], payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        notifications = []
        for rec in recommendations:
            title = (
                "Consider ordering lunch"
                if rec["meal"] == "lunch"
                else "Consider ordering dinner"
            )
            if rec["meal"] == "both":
                title = "Consider ordering lunch or dinner"
            notifications.append(
                {
                    "id": rec["id"],
                    "type": "recommendation",
                    "title": title,
                    "message": rec["message"],
                    "created_at": rec["generated_at"],
                    "metadata": {
                        "meal": rec["meal"],
                        "date": rec["date"],
                        "weekday": rec["weekday"],
                        "confidence": rec["confidence"],
                        "source": self.name,
                    },
                }
            )
        return notifications

    def _parse_dt(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    def _window_range(self, payload: Dict[str, Any], meal: str) -> Tuple[datetime, datetime]:
        day = date.fromisoformat(payload["date"])
        window = payload.get("meal_windows", {}).get(meal, {})

        start_time = window.get("start", "12:00" if meal == "lunch" else "18:00")
        end_time = window.get("end", "14:00" if meal == "lunch" else "20:30")

        start_dt = datetime.combine(day, time.fromisoformat(start_time))
        end_dt = datetime.combine(day, time.fromisoformat(end_time))
        return start_dt, end_dt

    def _busy_minutes_in_window(
        self, events: List[Tuple[datetime, datetime, str]], window: Tuple[datetime, datetime]
    ) -> float:
        start_window, end_window = window
        busy_minutes = 0.0
        for start, end, _ in events:
            overlap_start = max(start, start_window)
            overlap_end = min(end, end_window)
            if overlap_end > overlap_start:
                busy_minutes += (overlap_end - overlap_start).total_seconds() / 60
        return busy_minutes

    def _format_message(
        self,
        payload: Dict[str, Any],
        meal: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        weekday = payload.get("weekday") or "today"
        friendly_day = "today" if weekday == datetime.utcnow().strftime("%A") else weekday
        base = "lunch" if meal == "lunch" else "dinner"
        if meal == "both":
            base = "lunch or dinner"
        suffix = None
        if data:
            meal_label = data.get("meal")
            if meal_label and meal_label != "both" and meal_label == meal:
                suffix = data.get("message")
        if suffix:
            return suffix
        if meal == "lunch":
            return (
                f"{friendly_day} looks stacked around lunchtime—maybe order lunch so you can recharge without rushing."
            )
        if meal == "dinner":
            return (
                f"Your evening {friendly_day.lower()} is packed; consider ordering dinner so you can unwind when you finish."
            )
        return (
            f"{friendly_day} is busy—ordering something easy could keep you on track."
        )


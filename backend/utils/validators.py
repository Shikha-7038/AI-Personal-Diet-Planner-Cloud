"""Small, dependency-free input validators shared by routes and tests."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ALLOWED_DIET = {"vegan", "vegetarian", "general"}
ALLOWED_GOAL = {"balanced", "weight_management", "fitness"}
ALLOWED_ACTIVITY = {"sedentary", "light", "moderate", "active"}


class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def require_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("A valid email address is required")
    return email


def require_password(password: str) -> str:
    if not password or len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")
    return password


def require_name(name: str) -> str:
    name = (name or "").strip()
    if not (1 <= len(name) <= 80):
        raise ValidationError("Name must be between 1 and 80 characters")
    return name


def validate_profile_fields(data: dict) -> dict:
    out = {}
    if "name" in data:
        out["name"] = require_name(data["name"])
    if "sex" in data and data["sex"] is not None:
        if data["sex"] not in ("male", "female", "other"):
            raise ValidationError("sex must be male, female, or other")
        out["sex"] = data["sex"]
    for key, lo, hi in (("age", 10, 100), ("height", 100, 250), ("weight", 25, 300)):
        if key in data and data[key] is not None:
            try:
                val = float(data[key])
            except (TypeError, ValueError):
                raise ValidationError(f"{key} must be a number")
            if not (lo <= val <= hi):
                raise ValidationError(f"{key} must be between {lo} and {hi}")
            out[key] = val
    if "activity_level" in data and data["activity_level"] is not None:
        if data["activity_level"] not in ALLOWED_ACTIVITY:
            raise ValidationError(f"activity_level must be one of {sorted(ALLOWED_ACTIVITY)}")
        out["activity_level"] = data["activity_level"]
    if "dietary_preference" in data and data["dietary_preference"] is not None:
        if data["dietary_preference"] not in ALLOWED_DIET:
            raise ValidationError(f"dietary_preference must be one of {sorted(ALLOWED_DIET)}")
        out["dietary_preference"] = data["dietary_preference"]
    if "goal" in data and data["goal"] is not None:
        if data["goal"] not in ALLOWED_GOAL:
            raise ValidationError(f"goal must be one of {sorted(ALLOWED_GOAL)}")
        out["goal"] = data["goal"]
    if "allergies" in data:
        allergies = data["allergies"] or []
        if not isinstance(allergies, list) or not all(isinstance(a, str) for a in allergies):
            raise ValidationError("allergies must be a list of strings")
        out["allergies"] = [a.strip() for a in allergies if a.strip()][:20]
    if "preferences" in data and data["preferences"] is not None:
        out["preferences"] = str(data["preferences"]).strip()[:300]
    return out


def profile_is_complete(user: dict) -> bool:
    required = ("age", "height", "weight", "activity_level", "dietary_preference", "goal")
    return all(user.get(f) not in (None, "") for f in required)

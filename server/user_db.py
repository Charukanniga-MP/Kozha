"""User Data Database Module for Signify / Kozha.

Handles isolated storage per user for:
- Profile info
- Contacts (All, Favourites, Blocked)
- Call History & Missed Calls
- Notifications
- Avatar Settings
- Language & Preferences
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USER_DATA_FILE = DATA_DIR / "user_data.json"

_user_data_db: Dict[str, Dict[str, Any]] = {}


def _load_user_data() -> None:
    global _user_data_db
    if USER_DATA_FILE.exists():
        try:
            raw = json.loads(USER_DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                _user_data_db = raw
                return
        except Exception as exc:
            logger.warning("Error loading user_data.json: %s", exc)
    _user_data_db = {}


def _save_user_data() -> None:
    try:
        USER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        USER_DATA_FILE.write_text(json.dumps(_user_data_db, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to save user_data.json: %s", exc)


_load_user_data()


def get_default_user_data(user_id: str, email: str, name: str, phone: Optional[str] = None) -> Dict[str, Any]:
    """Generates initial data structure for a newly registered user."""
    clean_name = name or email.split("@")[0].capitalize()
    clean_phone = phone or "9876543210" if "charu" in email.lower() else "9834567290" if "keerthi" in email.lower() else "9000000000"

    # Default seed contacts based on role/account identity
    default_contacts = [
        {
            "id": "c_luna",
            "name": "Luna (Signify AI)",
            "phone": "+1 (800) 555-LUNA",
            "avatar": "/images/luna_3d.jpg",
            "isFav": True,
            "isBlocked": False
        }
    ]

    if "charu" in user_id.lower() or "charu" in email.lower():
        default_contacts.append({
            "id": "c_keerthi",
            "name": "Keerthi",
            "phone": "9834567290",
            "avatar": None,
            "isFav": True,
            "isBlocked": False
        })
        default_contacts.append({
            "id": "c_alex",
            "name": "Alex Rivers",
            "phone": "+1 (555) 019-2834",
            "avatar": None,
            "isFav": True,
            "isBlocked": False
        })
        default_contacts.append({
            "id": "c_priya",
            "name": "Priya",
            "phone": "9876543210",
            "avatar": None,
            "isFav": False,
            "isBlocked": False
        })
        default_contacts.append({
            "id": "c_sanjay",
            "name": "Sanjay",
            "phone": "9123456780",
            "avatar": None,
            "isFav": False,
            "isBlocked": False
        })
        default_contacts.append({
            "id": "c_meena",
            "name": "Meena",
            "phone": "9887766554",
            "avatar": None,
            "isFav": False,
            "isBlocked": False
        })
        default_contacts.append({
            "id": "c_ravi",
            "name": "Ravi Kumar",
            "phone": "9876012345",
            "avatar": None,
            "isFav": False,
            "isBlocked": True
        })
        default_contacts.append({
            "id": "c_spam",
            "name": "Spam Caller",
            "phone": "+1 (444) 222-9999",
            "avatar": None,
            "isFav": False,
            "isBlocked": True
        })

    elif "keerthi" in user_id.lower() or "keerthi" in email.lower():
        default_contacts.append({
            "id": "c_charu",
            "name": "Charu",
            "phone": "6382472844",
            "avatar": None,
            "isFav": True,
            "isBlocked": False
        })
        default_contacts.append({
            "id": "c_alex",
            "name": "Alex Rivers",
            "phone": "+1 (555) 019-2834",
            "avatar": None,
            "isFav": True,
            "isBlocked": False
        })
        default_contacts.append({
            "id": "c_sanjay",
            "name": "Sanjay",
            "phone": "9123456780",
            "avatar": None,
            "isFav": False,
            "isBlocked": False
        })

    default_history = [
        {
            "id": "h_1",
            "name": "Luna (Signify AI)",
            "phone": "+1 (800) 555-LUNA",
            "time": "Today, 10:45 AM",
            "type": "incoming",
            "avatar": "/images/luna_3d.jpg"
        }
    ]

    default_notifications = [
        {
            "id": "n_1",
            "title": "Welcome to Signify",
            "text": f"Hello {clean_name}! Your account has been initialized.",
            "time": "Just now",
            "read": False
        },
        {
            "id": "n_2",
            "title": "Avatar Ready",
            "text": "Your 3D full-body avatar is ready for sign language live calls.",
            "time": "1 hour ago",
            "read": True
        }
    ]

    return {
        "user_id": user_id,
        "profile": {
            "name": clean_name,
            "email": email,
            "phone": clean_phone,
            "role": "Sign Language User",
            "avatar": "/images/luna_3d.jpg" if "charu" in email.lower() else "/images/anna_3d.jpg"
        },
        "contacts": default_contacts,
        "callHistory": default_history,
        "notifications": default_notifications,
        "avatarSettings": {
            "selectedAvatar": "luna" if "charu" in email.lower() else "anna",
            "skinTone": "#F5D6BA",
            "hairStyle": "style_1",
            "hairColor": "#29231F",
            "eyeColor": "#16A34A",
            "outfit": "outfit_green",
            "pose": 0
        },
        "preferences": {
            "language": "en",
            "signLanguage": "bsl",
            "subtitles": True,
            "theme": "light"
        }
    }


def get_user_data(user_id: str, email: str = "", name: str = "") -> Dict[str, Any]:
    """Retrieves user data or initializes default if missing."""
    key = user_id.strip().lower()
    if key not in _user_data_db:
        _user_data_db[key] = get_default_user_data(user_id, email or user_id, name)
        _save_user_data()
    return _user_data_db[key]


def update_user_data(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Updates user data partially or fully and persists to disk."""
    key = user_id.strip().lower()
    current = _user_data_db.get(key, get_default_user_data(user_id, user_id, user_id))
    
    for field, val in updates.items():
        if isinstance(val, dict) and field in current and isinstance(current[field], dict):
            current[field].update(val)
        else:
            current[field] = val

    _user_data_db[key] = current
    _save_user_data()
    return current

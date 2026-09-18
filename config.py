import os
import re
from datetime import datetime
from functools import wraps

from flask import request, jsonify, g
from supabase import create_client, Client

# =========================================================
# Supabase clients
# =========================================================
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Service-role client: bypasses RLS. Only used server-side for operations
# that must run with elevated privilege (creating auth users, storage
# writes). NEVER send SUPABASE_SERVICE_KEY to a client/browser.
admin_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =========================================================
# Constants
# =========================================================
MAX_POST_IMAGES = 5
ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "webp"}
PROFILE_BUCKET = "profile-pictures"
POST_IMAGE_BUCKET = "post-images"


# =========================================================
# Helpers
# =========================================================
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXT


def make_password(last_name: str, birthday: str) -> str:
    """
    birthday expected as 'YYYY-MM-DD'. Produces e.g. 'delacruz10241995'.
    This is a TEMPORARY password only — the frontend should force a
    password change on first login.
    """
    clean_last = re.sub(r"\s+", "", last_name).lower()
    dt = datetime.strptime(birthday, "%Y-%m-%d")
    return f"{clean_last}{dt.strftime('%m%d%Y')}"


def get_user_client():
    """
    Builds a Supabase client scoped to the caller's own JWT, so every
    query made with it runs through RLS exactly as if the user made it
    directly (no privilege bypass on the read/write side).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None
    token = auth_header.split(" ", 1)[1]

    client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    try:
        user_resp = client.auth.get_user(token)
    except Exception:
        return None, None
    if not user_resp or not user_resp.user:
        return None, None

    client.postgrest.auth(token)
    return client, user_resp.user


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        client, user = get_user_client()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        g.supabase = client
        g.user = user
        return f(*args, **kwargs)
    return wrapper
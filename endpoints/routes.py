from datetime import datetime

from flask import Blueprint, request, jsonify, g

from config import (
    admin_client,
    allowed_file,
    make_password,
    require_auth,
    MAX_POST_IMAGES,
    PROFILE_BUCKET,
    POST_IMAGE_BUCKET,
)

api_bp = Blueprint("api", __name__)

# =========================================================
# GET /api/departments
# =========================================================
@api_bp.get("/api/departments")
@require_auth
def get_departments():
    result = admin_client.table("departments").select("*").execute()
    return jsonify(result.data), 200


# =========================================================
# GET /api/participants?filter=<department_id>
# =========================================================
@api_bp.get("/api/participants")
@require_auth
def get_participants():
    department_id = request.args.get("filter")

    query = g.supabase.table("participants").select(
        "id, first_name, last_name, email, birthday, gender, "
        "department_id, profile_path, access_level"
    )
    if department_id:
        query = query.eq("department_id", department_id)

    result = query.execute()
    return jsonify(result.data), 200


# =========================================================
# POST /api/register
# =========================================================
@api_bp.post("/api/register")
@require_auth
def register():
    data = request.get_json(silent=True) or {}
    required = ["first_name", "last_name", "email", "birthday", "department_id"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
 
    try:
        datetime.strptime(data["birthday"], "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "birthday must be in YYYY-MM-DD format"}), 400
 
    gender = data.get("gender")
    if gender is not None and gender not in ("male", "female"):
        return jsonify({"error": "gender must be 'male', 'female', or omitted"}), 400
 
    dept_check = admin_client.table("departments").select("id").eq(
        "id", data["department_id"]
    ).execute()
    if not dept_check.data:
        return jsonify({"error": "Invalid department_id"}), 400
 
    temp_password = make_password(data["last_name"], data["birthday"])
 
    try:
        created = admin_client.auth.admin.create_user({
            "email": data["email"],
            "password": temp_password,
            "email_confirm": True,
            "user_metadata": {
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "birthday": data["birthday"],
                "gender": gender,
                "department_id": data["department_id"],
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400
 
    # The participants row is created automatically by the
    # on_auth_user_created trigger defined in schema.sql.
    return jsonify({
        "message": "Registered successfully",
    }), 201


# =========================================================
# POST /api/profile-picture
# =========================================================
@api_bp.post("/api/profile-picture")
@require_auth
def upload_profile_picture():
    if "file" not in request.files:
        return jsonify({"error": "No file provided (expected form field 'file')"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or missing image file"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    path = f"{g.user.id}/profile.{ext}"

    try:
        admin_client.storage.from_(PROFILE_BUCKET).upload(
            path, file.read(),
            {"content-type": file.mimetype, "upsert": "true"},
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    result = g.supabase.table("participants").update(
        {"profile_path": path}
    ).eq("id", g.user.id).execute()

    return jsonify({
        "message": "Profile picture updated",
        "profile_path": path,
        "data": result.data,
    }), 200


# =========================================================
# POST /api/post
# =========================================================
@api_bp.post("/api/post")
@require_auth
def create_post():
    caption = request.form.get("caption")
    files = request.files.getlist("images")

    if not files or files[0].filename == "":
        return jsonify({"error": "At least 1 image is required"}), 400
    if len(files) > MAX_POST_IMAGES:
        return jsonify({"error": f"A maximum of {MAX_POST_IMAGES} images is allowed"}), 400
    for f in files:
        if not allowed_file(f.filename):
            return jsonify({"error": f"Invalid image type: {f.filename}"}), 400

    post_result = g.supabase.table("posts").insert({
        "posted_by": g.user.id,
        "caption": caption,
    }).execute()

    if not post_result.data:
        return jsonify({"error": "Failed to create post"}), 400

    post_id = post_result.data[0]["id"]
    uploaded_paths = []

    try:
        for i, file in enumerate(files):
            ext = file.filename.rsplit(".", 1)[1].lower()
            path = f"{g.user.id}/{post_id}/{i}.{ext}"
            admin_client.storage.from_(POST_IMAGE_BUCKET).upload(
                path, file.read(),
                {"content-type": file.mimetype, "upsert": "true"},
            )
            uploaded_paths.append(path)

        images_result = g.supabase.table("post_images").insert([
            {"post_id": post_id, "image_path": p} for p in uploaded_paths
        ]).execute()
    except Exception as e:
        # Roll back: remove the post (cascades to any inserted images)
        # and clean up any files that made it to storage.
        g.supabase.table("posts").delete().eq("id", post_id).execute()
        for p in uploaded_paths:
            admin_client.storage.from_(POST_IMAGE_BUCKET).remove([p])
        return jsonify({"error": f"Failed to create post: {e}"}), 400

    return jsonify({
        "message": "Post created",
        "post_id": post_id,
        "images": images_result.data,
    }), 201


# =========================================================
# GET /api/post
# =========================================================
@api_bp.get("/api/post")
@require_auth
def get_posts():
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    current_participant_id = g.user.id

    result = (
        g.supabase.table("posts")
        .select(
            """
            id,
            caption,
            created_at,
            author:participants!posts_posted_by_fkey(
                id,
                first_name,
                last_name,
                profile_path
            ),
            images:post_images(
                id,
                image_path
            ),
            post_likes(
                participant_id
            ),
            post_comments(
                id
            )
            """
        )
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    posts = []

    for post in result.data:
        likes = post.pop("post_likes", []) or []
        comments = post.pop("post_comments", []) or []
        images = post.get("images", []) or []

        author = post.get("author")

        posts.append({
            "id": post["id"],
            
            "author": {
                "id": author["id"],
                "first_name": author["first_name"],
                "last_name": author["last_name"],
                "profile_url": author["profile_path"]
            } if author else None,

            "images": [
                {
                    "id": image["id"],
                    "url": image["image_path"]
                }
                for image in images
            ],

            "caption": post["caption"],
            "likes_count": len(likes),
            "comments_count": len(comments),

            "liked_by_me": any(
                like["participant_id"] == current_participant_id
                for like in likes
            )
        })

    return jsonify({
        "data": posts
    }), 200

# =========================================================
# POST /api/like
# =========================================================
@api_bp.post("/api/like")
@require_auth
def like_post():
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    if not post_id:
        return jsonify({"error": "post_id is required"}), 400

    try:
        result = g.supabase.table("post_likes").insert({
            "post_id": post_id,
            "participant_id": g.user.id,
        }).execute()
    except Exception as e:
        # Most likely a duplicate like (composite primary key conflict)
        # or a post_id that doesn't exist.
        return jsonify({"error": "Already liked or invalid post_id", "detail": str(e)}), 400

    return jsonify({"message": "Post liked", "data": result.data}), 201
from flask import Flask, jsonify
from endpoints import api_bp
from config import SUPABASE_URL, SUPABASE_ANON_KEY


app = Flask(__name__)


app.register_blueprint(api_bp)


# =========================================================
# Make sure errors always come back as JSON, never an HTML
# page — otherwise fetch() on the frontend fails to parse
# the response (e.g. "Unexpected token '<'").
# =========================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


@app.get("/")
def read_root():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NAP Anniversary Event</title>
        <link rel="icon" type="image/svg+xml" href="/favicon.ico">
        <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                background-color: #000000; color: #ffffff; line-height: 1.6; min-height: 100vh;
                display: flex; flex-direction: column;
            }}
            main {{ flex: 1; max-width: 1200px; margin: 0 auto; padding: 4rem 2rem; display: flex; flex-direction: column; align-items: center; text-align: center; }}
            .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; width: 100%; max-width: 460px; text-align: left; }}
            .card {{ background-color: #111111; border: 1px solid #333333; border-radius: 8px; padding: 1.5rem; transition: all 0.2s ease; text-align: left; }}
            .card:hover {{ border-color: #555555; transform: translateY(-2px); }}
            .card h3 {{ font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem; color: #ffffff; }}
            .card p {{ color: #888888; font-size: 0.875rem; margin-bottom: 1rem; }}
            pre {{ background-color: #0a0a0a; border: 1px solid #333333; border-radius: 6px; padding: 1rem; overflow-x: auto; margin: 0; }}
            code {{ font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace; font-size: 0.85rem; line-height: 1.5; color: #ffffff; }}
            .login-form {{ display: flex; flex-direction: column; gap: 0.6rem; }}
            .login-form input {{
                padding: 0.6rem 0.75rem; border-radius: 6px; border: 1px solid #333333;
                background-color: #0a0a0a; color: #ffffff; font-size: 0.875rem;
            }}
            .login-form input:focus {{ outline: none; border-color: #555555; }}
            .login-form button {{
                padding: 0.6rem; border-radius: 6px; border: 1px solid #333333;
                background-color: #222222; color: #ffffff; font-size: 0.875rem;
                font-weight: 500; cursor: pointer; transition: all 0.2s ease;
            }}
            .login-form button:hover {{ background-color: #333333; border-color: #555555; }}
            .login-form button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            #token-output {{ margin-top: 1rem; display: none; }}
            #token-text {{ display: block; }}
            #copy-btn {{
                margin-top: 0.6rem; width: 100%; padding: 0.5rem; border-radius: 6px;
                border: 1px solid #333333; background-color: #222222; color: #ffffff;
                font-size: 0.8rem; font-weight: 500; cursor: pointer; transition: all 0.2s ease;
            }}
            #copy-btn:hover {{ background-color: #333333; border-color: #555555; }}
            #token-error {{ color: #ff6b6b; font-size: 0.8rem; margin-top: 0.5rem; display: none; }}
            @media (max-width: 768px) {{
                main {{ padding: 2rem 1rem; }}
                .cards {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <main>
            <div class="cards">
                <div class="card">
                    <h3>Login (Get JWT)</h3>
                    <p>Signs in directly against Supabase Auth (not the Flask API) and returns an access token for testing the authenticated endpoints.</p>
                    <form id="login-form" class="login-form">
                        <input type="email" id="email" placeholder="Email" required />
                        <input type="password" id="password" placeholder="Password" required />
                        <button type="submit" id="login-btn">Login</button>
                    </form>
                    <div id="token-error"></div>
                    <pre id="token-output"><code id="token-text"></code></pre>
                    <button id="copy-btn" style="display: none;">Copy token</button>
                </div>
            </div>
        </main>

        <script>
            var supabaseClient = supabase.createClient(
                "{SUPABASE_URL}",
                "{SUPABASE_ANON_KEY}"
            );

            var copyBtn = document.getElementById('copy-btn');

            document.getElementById('login-form').addEventListener('submit', async function (e) {{
                e.preventDefault();

                var btn = document.getElementById('login-btn');
                var output = document.getElementById('token-output');
                var tokenText = document.getElementById('token-text');
                var errorBox = document.getElementById('token-error');

                errorBox.style.display = 'none';
                output.style.display = 'none';
                copyBtn.style.display = 'none';
                btn.disabled = true;
                btn.textContent = 'Logging in...';

                var email = document.getElementById('email').value;
                var password = document.getElementById('password').value;

                var {{ data, error }} = await supabaseClient.auth.signInWithPassword({{
                    email: email,
                    password: password
                }});

                btn.disabled = false;
                btn.textContent = 'Login';

                if (error) {{
                    errorBox.textContent = error.message;
                    errorBox.style.display = 'block';
                    return;
                }}

                tokenText.textContent = data.session.access_token;
                output.style.display = 'block';
                copyBtn.style.display = 'block';
                copyBtn.textContent = 'Copy token';
            }});

            copyBtn.addEventListener('click', async function () {{
                var token = document.getElementById('token-text').textContent;
                try {{
                    await navigator.clipboard.writeText(token);
                    copyBtn.textContent = 'Copied!';
                }} catch (err) {{
                    copyBtn.textContent = 'Copy failed — select manually';
                }}
                setTimeout(function () {{ copyBtn.textContent = 'Copy token'; }}, 1500);
            }});
        </script>
    </body>
    </html>
    """

@app.get("/api/docs")
def api_docs():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NAP Anniversary Event — API Docs</title>

        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                    'Roboto', sans-serif;
                background-color: #000000;
                color: #ffffff;
                line-height: 1.6;
            }

            header {
                padding: 2.5rem 2rem 1.5rem;
                max-width: 900px;
                margin: 0 auto;
                border-bottom: 1px solid #222222;
            }

            header h1 {
                font-size: 1.75rem;
                margin-bottom: 0.4rem;
            }

            header p {
                color: #888888;
                font-size: 0.9rem;
            }

            main {
                max-width: 900px;
                margin: 0 auto;
                padding: 2rem;
            }

            .endpoint {
                background-color: #111111;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }

            .endpoint-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 0.75rem;
                flex-wrap: wrap;
            }

            .method {
                font-size: 0.75rem;
                font-weight: 700;
                padding: 0.2rem 0.6rem;
                border-radius: 4px;
                letter-spacing: 0.03em;
            }

            .method.get {
                background-color: #1e3a2e;
                color: #4ade80;
            }

            .method.post {
                background-color: #1e2a3a;
                color: #60a5fa;
            }

            .method.put {
                background-color: #3a321e;
                color: #fbbf24;
            }

            .method.delete {
                background-color: #3a1e1e;
                color: #f87171;
            }

            .path {
                font-family: 'SF Mono', Monaco, Consolas, monospace;
                font-size: 0.95rem;
                color: #ffffff;
            }

            .auth-badge {
                font-size: 0.7rem;
                color: #fbbf24;
                border: 1px solid #4a3c1a;
                background-color: #1a1608;
                padding: 0.15rem 0.5rem;
                border-radius: 4px;
                margin-left: auto;
            }

            .public-badge {
                font-size: 0.7rem;
                color: #4ade80;
                border: 1px solid #1f4a32;
                background-color: #0d1f15;
                padding: 0.15rem 0.5rem;
                border-radius: 4px;
                margin-left: auto;
            }

            .desc {
                color: #aaaaaa;
                font-size: 0.875rem;
                margin-bottom: 1rem;
            }

            h4 {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #888888;
                margin: 0.9rem 0 0.4rem;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.85rem;
                margin-bottom: 0.5rem;
            }

            th,
            td {
                text-align: left;
                padding: 0.4rem 0.5rem;
                border-bottom: 1px solid #222222;
            }

            th {
                color: #888888;
                font-weight: 500;
            }

            td code {
                font-family: 'SF Mono', Monaco, Consolas, monospace;
                color: #93c5fd;
            }

            pre {
                background-color: #0a0a0a;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 1rem;
                overflow-x: auto;
                font-size: 0.8rem;
                margin-top: 0.4rem;
            }

            code.block {
                font-family: 'SF Mono', Monaco, Consolas, monospace;
                color: #d1d5db;
                white-space: pre;
            }

            nav {
                position: sticky;
                top: 0;
                background: #000000;
                border-bottom: 1px solid #222222;
                padding: 0.75rem 2rem;
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
                z-index: 10;
                justify-content: center;
            }

            nav a {
                color: #888888;
                font-size: 0.8rem;
                text-decoration: none;
            }

            nav a:hover {
                color: #ffffff;
            }

            .note {
                background-color: #111111;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                color: #aaaaaa;
                font-size: 0.85rem;
            }

            .note strong {
                color: #ffffff;
            }
        </style>
    </head>

    <body>

        <header>
            <h1>NAP Anniversary Event API</h1>
            <p>
                Reference for frontend integration.
                Unless noted as "No auth", every endpoint requires a Supabase JWT in
                <code style="color:#93c5fd">
                    Authorization: Bearer &lt;token&gt;
                </code>.
            </p>
        </header>

        <nav>
            <a href="#departments">Departments</a>
            <a href="#participants">Participants</a>
            <a href="#register">Register</a>
            <a href="#profile-picture">Profile Picture</a>
            <a href="#post-create">Create Post</a>
            <a href="#post-list">List Posts</a>
            <a href="#post-delete">Delete Post</a>
            <a href="#post-likes">View Likes</a>
            <a href="#post-comments">View Comments</a>
            <a href="#like">Like Post</a>
            <a href="#unlike">Unlike Post</a>
            <a href="#comment-create">Create Comment</a>
            <a href="#comment-update">Update Comment</a>
            <a href="#comment-delete">Delete Comment</a>
        </nav>

        <main>

            <div class="note">
                <strong>Authentication:</strong>
                Protected endpoints require:
                <code>Authorization: Bearer &lt;supabase_access_token&gt;</code>.
                The registration endpoint and department listing endpoint are public.
            </div>

            <!-- ===================================================== -->
            <!-- DEPARTMENTS -->
            <!-- ===================================================== -->

            <div class="endpoint" id="departments">

                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span class="path">/api/departments</span>
                    <span class="public-badge">No auth</span>
                </div>

                <p class="desc">
                    Returns all departments. This endpoint is public so the
                    registration form can populate the department dropdown before
                    the guest has an account.
                </p>

                <h4>Response 200</h4>

                <pre><code class="block">[
  {
    "id": "3f2b1a10-...",
    "name": "IT"
  },
  {
    "id": "7c9e4d20-...",
    "name": "Trademark"
  }
]</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- PARTICIPANTS -->
            <!-- ===================================================== -->

            <div class="endpoint" id="participants">

                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span class="path">/api/participants</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Returns participants, optionally filtered by department.
                    Super admins receive additional participant fields.
                </p>

                <h4>Query params</h4>

                <table>
                    <tr>
                        <th>Param</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>filter</code></td>
                        <td>uuid</td>
                        <td>No</td>
                        <td>Department ID to filter by</td>
                    </tr>
                </table>

                <h4>Response 200 — Regular user</h4>

                <pre><code class="block">[
  {
    "id": "uuid",
    "first_name": "Jane",
    "last_name": "Doe",
    "gender": "female",
    "department_id": "uuid",
    "profile_path": "uuid/profile.jpg"
  }
]</code></pre>

                <h4>Response 200 — Super admin</h4>

                <pre><code class="block">[
  {
    "id": "uuid",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "birthday": "1990-01-01",
    "gender": "female",
    "department_id": "uuid",
    "profile_path": "uuid/profile.jpg",
    "access_level": "guest"
  }
]</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- REGISTER -->
            <!-- ===================================================== -->

            <div class="endpoint" id="register">

                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span class="path">/auth/register</span>
                    <span class="public-badge">No auth</span>
                </div>

                <p class="desc">
                    Creates a new Supabase Auth user. The participant row is
                    automatically created by the
                    <code>on_auth_user_created</code> database trigger.
                    A temporary password is generated from the user's last name
                    and birth year.
                </p>

                <h4>Body (JSON)</h4>

                <table>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>first_name</code></td>
                        <td>string</td>
                        <td>Yes</td>
                        <td>Participant first name</td>
                    </tr>

                    <tr>
                        <td><code>last_name</code></td>
                        <td>string</td>
                        <td>Yes</td>
                        <td>Used to derive temporary password</td>
                    </tr>

                    <tr>
                        <td><code>email</code></td>
                        <td>string</td>
                        <td>Yes</td>
                        <td>User email address</td>
                    </tr>

                    <tr>
                        <td><code>birthday</code></td>
                        <td>string</td>
                        <td>Yes</td>
                        <td>Format <code>YYYY-MM-DD</code></td>
                    </tr>

                    <tr>
                        <td><code>department_id</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>Must exist in <code>departments</code></td>
                    </tr>

                    <tr>
                        <td><code>gender</code></td>
                        <td>string</td>
                        <td>No</td>
                        <td><code>"male"</code>, <code>"female"</code>, or omitted</td>
                    </tr>
                </table>

                <h4>Example request</h4>

                <pre><code class="block">{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@example.com",
  "birthday": "1990-01-01",
  "department_id": "3f2b1a10-...",
  "gender": "female"
}</code></pre>

                <h4>Response 201</h4>

                <pre><code class="block">{
  "message": "Registered successfully"
}</code></pre>

                <h4>Errors 400</h4>

                <pre><code class="block">{
  "error": "Missing required fields: email, department_id"
}

{
  "error": "birthday must be in YYYY-MM-DD format"
}

{
  "error": "gender must be 'male', 'female', or omitted"
}

{
  "error": "Invalid department_id"
}</code></pre>

                <h4>Error 409</h4>

                <pre><code class="block">{
  "error": "This person has already registered"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- PROFILE -->
            <!-- ===================================================== -->

            <div class="endpoint" id="profile-picture">

                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span class="path">/api/profile-picture</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Uploads or replaces the authenticated user's profile picture.
                </p>

                <h4>Body (multipart/form-data)</h4>

                <table>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>file</code></td>
                        <td>file</td>
                        <td>Yes</td>
                        <td>
                            Image file. Supported extensions:
                            jpg, jpeg, png, webp
                        </td>
                    </tr>
                </table>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "message": "Profile picture updated",
  "profile_path": "uuid/profile.jpg",
  "data": [ ... ]
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- CREATE POST -->
            <!-- ===================================================== -->

            <div class="endpoint" id="post-create">

                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span class="path">/api/post</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Creates a post with one or more images. If image upload or
                    database insertion fails, the post and uploaded images are
                    rolled back.
                </p>

                <h4>Body (multipart/form-data)</h4>

                <table>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>caption</code></td>
                        <td>string</td>
                        <td>No</td>
                        <td>Post caption</td>
                    </tr>

                    <tr>
                        <td><code>images</code></td>
                        <td>file[]</td>
                        <td>Yes</td>
                        <td>
                            1–5 images. Repeat the <code>images</code>
                            field for each image.
                        </td>
                    </tr>
                </table>

                <h4>Supported image types</h4>

                <pre><code class="block">jpg
jpeg
png
webp</code></pre>

                <h4>Response 201</h4>

                <pre><code class="block">{
  "message": "Post created",
  "post_id": "uuid",
  "images": [
    {
      "id": "uuid",
      "post_id": "uuid",
      "image_path": "uuid/postid/0.jpg"
    }
  ]
}</code></pre>

                <h4>Errors 400</h4>

                <pre><code class="block">{
  "error": "Expected multipart/form-data"
}

{
  "error": "At least 1 image is required"
}

{
  "error": "A maximum of 5 images is allowed"
}

{
  "error": "Invalid image type: photo.exe"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- LIST POSTS -->
            <!-- ===================================================== -->

            <div class="endpoint" id="post-list">

                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span class="path">/api/post</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Returns a paginated feed of posts with author information,
                    images, like count, comment count, and whether the current
                    user liked each post.
                </p>

                <h4>Query params</h4>

                <table>
                    <tr>
                        <th>Param</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>limit</code></td>
                        <td>int</td>
                        <td>No</td>
                        <td>Default 20, minimum 1, maximum 100</td>
                    </tr>

                    <tr>
                        <td><code>offset</code></td>
                        <td>int</td>
                        <td>No</td>
                        <td>Default 0</td>
                    </tr>
                </table>

                <h4>Example</h4>

                <pre><code class="block">GET /api/post?limit=20&amp;offset=0</code></pre>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "data": [
    {
      "id": "uuid",

      "author": {
        "id": "uuid",
        "first_name": "Jane",
        "last_name": "Doe",
        "profile_url": "uuid/profile.jpg"
      },

      "images": [
        {
          "id": "uuid",
          "url": "uuid/postid/0.jpg"
        }
      ],

      "caption": "Hello!",
      "likes_count": 3,
      "comments_count": 1,
      "liked_by_me": true
    }
  ]
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- DELETE POST -->
            <!-- ===================================================== -->

            <div class="endpoint" id="post-delete">

                <div class="endpoint-header">
                    <span class="method delete">DELETE</span>
                    <span class="path">/api/post/:postId</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Deletes a post and its associated post images.
                    Only the post author or an admin can delete the post.
                </p>

                <h4>Path params</h4>

                <table>
                    <tr>
                        <th>Param</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>postId</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the post to delete</td>
                    </tr>
                </table>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "message": "Post deleted"
}</code></pre>

                <h4>Error 404</h4>

                <pre><code class="block">{
  "error": "Post not found or you don't have permission to delete it"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- VIEW POST LIKES -->
            <!-- ===================================================== -->

            <div class="endpoint" id="post-likes">

                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span class="path">/api/post/:postId/likes</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Returns the participants who liked a specific post,
                    including their name, profile picture path, and like timestamp.
                </p>

                <h4>Path params</h4>

                <table>
                    <tr>
                        <th>Param</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>postId</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the post</td>
                    </tr>
                </table>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "data": [
    {
      "created_at": "2026-09-21T10:30:00+00:00",
      "participant": {
        "id": "uuid",
        "first_name": "Jane",
        "last_name": "Doe",
        "profile_path": "uuid/profile.jpg"
      }
    }
  ]
}</code></pre>

                <p class="desc">
                    Results are ordered by newest like first.
                </p>

                <h4>Error 404</h4>

                <pre><code class="block">{
  "error": "Post not found"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- VIEW POST COMMENTS -->
            <!-- ===================================================== -->

            <div class="endpoint" id="post-comments">

                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span class="path">/api/post/:postId/comments</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Returns all comments for a specific post, including the
                    participant who made each comment.
                </p>

                <h4>Path params</h4>

                <table>
                    <tr>
                        <th>Param</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>postId</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the post</td>
                    </tr>
                </table>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "data": [
    {
      "id": "uuid",
      "comment": "Great post!",
      "created_at": "2026-09-21T10:30:00+00:00",
      "participant": {
        "id": "uuid",
        "first_name": "Jane",
        "last_name": "Doe",
        "profile_path": "uuid/profile.jpg"
      }
    }
  ]
}</code></pre>

                <p class="desc">
                    Results are ordered from oldest comment to newest comment.
                </p>

                <h4>Error 404</h4>

                <pre><code class="block">{
  "error": "Post not found"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- LIKE -->
            <!-- ===================================================== -->

            <div class="endpoint" id="like">

                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span class="path">/api/like</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Likes a post on behalf of the current authenticated user.
                    A user can only like the same post once.
                </p>

                <h4>Body (JSON)</h4>

                <table>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>post_id</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the post</td>
                    </tr>
                </table>

                <h4>Example request</h4>

                <pre><code class="block">{
  "post_id": "uuid"
}</code></pre>

                <h4>Response 201</h4>

                <pre><code class="block">{
  "message": "Post liked",
  "data": [
    {
      "post_id": "uuid",
      "participant_id": "uuid"
    }
  ]
}</code></pre>

                <h4>Errors 400</h4>

                <pre><code class="block">{
  "error": "post_id is required"
}

{
  "error": "Already liked or invalid post_id",
  "detail": "..."
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- UNLIKE -->
            <!-- ===================================================== -->

            <div class="endpoint" id="unlike">

                <div class="endpoint-header">
                    <span class="method delete">DELETE</span>
                    <span class="path">/api/like</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Removes the authenticated user's like from a post.
                </p>

                <h4>Body (JSON)</h4>

                <table>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>post_id</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the post</td>
                    </tr>
                </table>

                <h4>Alternative</h4>

                <p class="desc">
                    <code>post_id</code> can also be supplied as a query parameter.
                </p>

                <pre><code class="block">DELETE /api/like?post_id=uuid</code></pre>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "message": "Post unliked"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- CREATE COMMENT -->
            <!-- ===================================================== -->

            <div class="endpoint" id="comment-create">

                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span class="path">/api/comment</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Creates a comment on a post using the authenticated user's
                    participant ID.
                </p>

                <h4>Body (JSON)</h4>

                <table>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>post_id</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the post</td>
                    </tr>

                    <tr>
                        <td><code>comment</code></td>
                        <td>string</td>
                        <td>Yes</td>
                        <td>Comment content</td>
                    </tr>
                </table>

                <h4>Example request</h4>

                <pre><code class="block">{
  "post_id": "uuid",
  "comment": "Great post!"
}</code></pre>

                <h4>Response 201</h4>

                <pre><code class="block">{
  "message": "Comment created",
  "data": {
    "id": "uuid",
    "post_id": "uuid",
    "participant_id": "uuid",
    "comment": "Great post!",
    "created_at": "2026-09-21T10:30:00+00:00"
  }
}</code></pre>

                <h4>Error 400</h4>

                <pre><code class="block">{
  "error": "post_id and comment are required"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- UPDATE COMMENT -->
            <!-- ===================================================== -->

            <div class="endpoint" id="comment-update">

                <div class="endpoint-header">
                    <span class="method put">PUT</span>
                    <span class="path">/api/comment/:commentId</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Updates a comment. Only the comment's author can edit it.
                </p>

                <h4>Path params</h4>

                <table>
                    <tr>
                        <th>Param</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>commentId</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the comment</td>
                    </tr>
                </table>

                <h4>Body (JSON)</h4>

                <pre><code class="block">{
  "comment": "Updated comment"
}</code></pre>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "message": "Comment updated",
  "data": {
    "id": "uuid",
    "post_id": "uuid",
    "participant_id": "uuid",
    "comment": "Updated comment",
    "created_at": "2026-09-21T10:30:00+00:00"
  }
}</code></pre>

                <h4>Error 404</h4>

                <pre><code class="block">{
  "error": "Comment not found or you don't have permission to edit it"
}</code></pre>

            </div>


            <!-- ===================================================== -->
            <!-- DELETE COMMENT -->
            <!-- ===================================================== -->

            <div class="endpoint" id="comment-delete">

                <div class="endpoint-header">
                    <span class="method delete">DELETE</span>
                    <span class="path">/api/comment/:commentId</span>
                    <span class="auth-badge">Auth required</span>
                </div>

                <p class="desc">
                    Deletes a comment. Only the comment's author can delete it.
                </p>

                <h4>Path params</h4>

                <table>
                    <tr>
                        <th>Param</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Notes</th>
                    </tr>

                    <tr>
                        <td><code>commentId</code></td>
                        <td>uuid</td>
                        <td>Yes</td>
                        <td>ID of the comment</td>
                    </tr>
                </table>

                <h4>Response 200</h4>

                <pre><code class="block">{
  "message": "Comment deleted"
}</code></pre>

                <h4>Error 404</h4>

                <pre><code class="block">{
  "error": "Comment not found or you don't have permission to delete it"
}</code></pre>

            </div>

        </main>

    </body>
    </html>
    """
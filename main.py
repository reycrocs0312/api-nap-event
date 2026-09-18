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
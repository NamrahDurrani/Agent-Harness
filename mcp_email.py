# """
# mcp_email.py
# ============
# MCP Tool: Send welcome email when a user registers on AgriBot.

# Architecture:
#     POST /api/auth/register
#         → auth_routes.py creates user
#         → calls mcp_send_welcome_email(username, email)
#         → this module sends SMTP email via Gmail App Password

# Setup (one-time):
#     1. In Gmail: Settings → Security → 2-Step Verification → App Passwords
#        Create an app password for "Mail" → copy the 16-char password
#     2. Set environment variables:
#          AGRIBOT_EMAIL_FROM=youragribot@gmail.com
#          AGRIBOT_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx   (16-char app password)
#     3. Optionally:
#          AGRIBOT_EMAIL_ENABLED=true   (set to "false" to disable without removing vars)

# Terminal setup (Windows PowerShell):
#     $env:AGRIBOT_EMAIL_FROM="youragribot@gmail.com"
#     $env:AGRIBOT_EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
#     $env:AGRIBOT_EMAIL_ENABLED="true"

# Terminal setup (Linux/Mac):
#     export AGRIBOT_EMAIL_FROM="youragribot@gmail.com"
#     export AGRIBOT_EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
#     export AGRIBOT_EMAIL_ENABLED="true"

# If env vars are not set, the function logs a warning and returns — it will
# NEVER crash the registration flow even if email sending fails.
# """

# import os
# import smtplib
# import traceback
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from datetime import datetime

# # ── Config from environment ────────────────────────────────────────────────────
# _FROM    = os.environ.get("AGRIBOT_EMAIL_FROM", "")
# _PASS    = os.environ.get("AGRIBOT_EMAIL_PASSWORD", "")
# _ENABLED = os.environ.get("AGRIBOT_EMAIL_ENABLED", "true").lower() == "true"

# _SMTP_HOST = "smtp.gmail.com"
# _SMTP_PORT = 587


# # ── Email HTML template ────────────────────────────────────────────────────────
# def _build_html(username: str) -> str:
#     year = datetime.now().year
#     return f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#   <meta charset="UTF-8">
#   <meta name="viewport" content="width=device-width, initial-scale=1.0">
#   <title>Welcome to AgriBot</title>
# </head>
# <body style="margin:0;padding:0;background:#f0f7ec;font-family:'Segoe UI',Arial,sans-serif;">
#   <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ec;padding:40px 20px;">
#     <tr><td align="center">
#       <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(60,100,30,0.10);">

#         <!-- Header -->
#         <tr><td style="background:#1a3a0a;padding:32px 40px;text-align:center;">
#           <div style="font-size:48px;margin-bottom:12px;">🌾</div>
#           <h1 style="color:#7ab648;font-size:26px;font-weight:800;margin:0 0 6px;letter-spacing:-0.5px;">AgriBot</h1>
#           <p style="color:#7a9460;font-size:14px;margin:0;">Agricultural Knowledge Assistant</p>
#         </td></tr>

#         <!-- Body -->
#         <tr><td style="padding:36px 40px;">
#           <h2 style="color:#1a3a0a;font-size:20px;font-weight:700;margin:0 0 16px;">Welcome, {username}! 👋</h2>
#           <p style="color:#3a5020;font-size:15px;line-height:1.7;margin:0 0 20px;">
#             Your AgriBot account has been successfully created. You now have access to Pakistan's most intelligent agricultural knowledge assistant.
#           </p>

#           <!-- Feature cards -->
#           <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
#             <tr>
#               <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
#                 <div style="font-size:22px;margin-bottom:8px;">📚</div>
#                 <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">RAG Knowledge Base</div>
#                 <div style="font-size:12px;color:#6a9450;line-height:1.5;">PARC Reports, FAO Guidelines, Punjab Agriculture Rules — all searchable.</div>
#               </td>
#               <td width="4%"></td>
#               <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
#                 <div style="font-size:22px;margin-bottom:8px;">🌐</div>
#                 <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">Live Web Search</div>
#                 <div style="font-size:12px;color:#6a9450;line-height:1.5;">When the answer isn't in the docs, we search trusted Pakistani sources live.</div>
#               </td>
#             </tr>
#             <tr><td colspan="3" height="12"></td></tr>
#             <tr>
#               <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
#                 <div style="font-size:22px;margin-bottom:8px;">⚡</div>
#                 <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">MCP Tools</div>
#                 <div style="font-size:12px;color:#6a9450;line-height:1.5;">Real-time weather, crop calendar, unit converter, market prices.</div>
#               </td>
#               <td width="4%"></td>
#               <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
#                 <div style="font-size:22px;margin-bottom:8px;">📁</div>
#                 <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">Project Management</div>
#                 <div style="font-size:12px;color:#6a9450;line-height:1.5;">Organise your research into projects. Upload your own PDFs.</div>
#               </td>
#             </tr>
#           </table>

#           <!-- Privacy notice -->
#           <div style="background:#fff8e8;border:1px solid #e0c070;border-radius:10px;padding:14px 18px;margin-bottom:24px;">
#             <div style="font-size:13px;font-weight:700;color:#8a5800;margin-bottom:4px;">🔒 Privacy Notice</div>
#             <div style="font-size:12.5px;color:#6a4000;line-height:1.6;">
#               You are sharing your account information with AgriBot for the purpose of accessing agricultural knowledge services. We do not share your data with third parties. Your conversations are stored locally on our server to enable conversation history.
#             </div>
#           </div>

#           <p style="color:#3a5020;font-size:14px;line-height:1.7;margin:0 0 24px;">
#             You can start asking questions immediately. Try: <em style="color:#4a8a1e;">"What wheat diseases are common in Punjab?"</em> or <em style="color:#4a8a1e;">"Is tomorrow a good day for sowing in Lahore?"</em>
#           </p>

#           <!-- CTA -->
#           <div style="text-align:center;">
#             <a href="http://localhost:5173" style="display:inline-block;background:#4a8a1e;color:#ffffff;font-size:14px;font-weight:700;padding:13px 32px;border-radius:10px;text-decoration:none;letter-spacing:0.01em;">Open AgriBot →</a>
#           </div>
#         </td></tr>

#         <!-- Footer -->
#         <tr><td style="background:#f0f7ec;border-top:1px solid #c8dab8;padding:20px 40px;text-align:center;">
#           <p style="color:#6a9450;font-size:11.5px;margin:0;line-height:1.6;">
#             AgriBot · Agricultural Knowledge Assistant for Pakistan<br>
#             © {year} AgriBot. Powered by Groq + ChromaDB + Tavily.<br>
#             <span style="color:#aaa;">If you did not register for this account, please ignore this email.</span>
#           </p>
#         </td></tr>

#       </table>
#     </td></tr>
#   </table>
# </body>
# </html>"""


# def _build_plain(username: str) -> str:
#     return f"""Welcome to AgriBot, {username}!

# Your AgriBot account has been successfully created.

# AgriBot is Pakistan's Agricultural Knowledge Assistant powered by:
# - RAG knowledge base (PARC Reports, FAO Guidelines, Punjab Agriculture Rules)
# - Live web search via Tavily
# - MCP tools: weather, crop calendar, unit converter
# - Project management: organise research, upload your own PDFs

# PRIVACY NOTICE:
# You are sharing your account information with AgriBot for agricultural knowledge services.
# We do not share your data with third parties.

# Start now at: http://localhost:5173

# ---
# AgriBot · Agricultural Knowledge Assistant
# If you did not register, please ignore this email.
# """


# # ── Main function ─────────────────────────────────────────────────────────────

# def mcp_send_welcome_email(username: str, email: str) -> dict:
#     """
#     MCP Tool: Send a welcome email to a newly registered AgriBot user.

#     Called from auth_routes.py after successful registration.
#     Never raises — always returns a result dict.

#     Returns:
#         {"status": "sent",    "to": email}
#         {"status": "skipped", "reason": "..."}
#         {"status": "error",   "error": "..."}
#     """
#     if not email or "@" not in email:
#         return {"status": "skipped", "reason": "No valid email address provided"}

#     if not _ENABLED:
#         print(f"[MCP/email] Disabled (AGRIBOT_EMAIL_ENABLED != true). Would send to {email}")
#         return {"status": "skipped", "reason": "Email sending disabled"}

#     if not _FROM or not _PASS:
#         print(
#             "[MCP/email] AGRIBOT_EMAIL_FROM or AGRIBOT_EMAIL_PASSWORD not set.\n"
#             "  Set them in your .env or terminal:\n"
#             "    export AGRIBOT_EMAIL_FROM=youragribot@gmail.com\n"
#             "    export AGRIBOT_EMAIL_PASSWORD='xxxx xxxx xxxx xxxx'"
#         )
#         return {"status": "skipped", "reason": "Email credentials not configured"}

#     try:
#         msg = MIMEMultipart("alternative")
#         msg["Subject"] = "🌾 Welcome to AgriBot — Your Agricultural Knowledge Assistant"
#         msg["From"]    = f"AgriBot <{_FROM}>"
#         msg["To"]      = email

#         msg.attach(MIMEText(_build_plain(username), "plain"))
#         msg.attach(MIMEText(_build_html(username),  "html"))

#         with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as server:
#             server.ehlo()
#             server.starttls()
#             server.login(_FROM, _PASS)
#             server.sendmail(_FROM, [email], msg.as_string())

#         print(f"[MCP/email] ✓ Welcome email sent → {email} (user: {username})")
#         return {"status": "sent", "to": email}

#     except smtplib.SMTPAuthenticationError:
#         msg = "Gmail authentication failed. Make sure you're using an App Password, not your regular password."
#         print(f"[MCP/email] ✗ {msg}")
#         return {"status": "error", "error": msg}

#     except Exception as e:
#         print(f"[MCP/email] ✗ Failed: {e}\n{traceback.format_exc()}")
#         return {"status": "error", "error": str(e)}




"""
mcp_email.py
============
MCP Tool: Send welcome email when a user registers on AgriBot.

Architecture:
    POST /api/auth/register
        → auth_routes.py creates user
        → calls mcp_send_welcome_email(username, email)
        → this module sends SMTP email via Gmail App Password

Setup (one-time):
    1. In Gmail: Settings → Security → 2-Step Verification → App Passwords
       Create an app password for "Mail" → copy the 16-char password
    2. Set environment variables:
         AGRIBOT_EMAIL_FROM=youragribot@gmail.com
         AGRIBOT_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx   (16-char app password)
    3. Optionally:
         AGRIBOT_EMAIL_ENABLED=true   (set to "false" to disable without removing vars)

Terminal setup (Windows PowerShell):
    $env:AGRIBOT_EMAIL_FROM="youragribot@gmail.com"
    $env:AGRIBOT_EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
    $env:AGRIBOT_EMAIL_ENABLED="true"

Terminal setup (Linux/Mac):
    export AGRIBOT_EMAIL_FROM="youragribot@gmail.com"
    export AGRIBOT_EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
    export AGRIBOT_EMAIL_ENABLED="true"

If env vars are not set, the function logs a warning and returns — it will
NEVER crash the registration flow even if email sending fails.
"""

import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ── Config from environment ────────────────────────────────────────────────────
_FROM    = os.environ.get("AGRIBOT_EMAIL_FROM", "")
_PASS    = os.environ.get("AGRIBOT_EMAIL_PASSWORD", "")
_ENABLED = os.environ.get("AGRIBOT_EMAIL_ENABLED", "true").lower() == "true"

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


# ── Email HTML template ────────────────────────────────────────────────────────
def _build_html(username: str) -> str:
    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to AgriBot</title>
</head>
<body style="margin:0;padding:0;background:#f0f7ec;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ec;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(60,100,30,0.10);">

        <!-- Header -->
        <tr><td style="background:#1a3a0a;padding:32px 40px;text-align:center;">
          <div style="font-size:48px;margin-bottom:12px;">🌾</div>
          <h1 style="color:#7ab648;font-size:26px;font-weight:800;margin:0 0 6px;letter-spacing:-0.5px;">AgriBot</h1>
          <p style="color:#7a9460;font-size:14px;margin:0;">Agricultural Knowledge Assistant</p>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:36px 40px;">
          <h2 style="color:#1a3a0a;font-size:20px;font-weight:700;margin:0 0 16px;">Welcome, {username}! 👋</h2>
          <p style="color:#3a5020;font-size:15px;line-height:1.7;margin:0 0 20px;">
            Your AgriBot account has been successfully created. You now have access to Pakistan's most intelligent agricultural knowledge assistant.
          </p>

          <!-- Feature cards -->
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
            <tr>
              <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
                <div style="font-size:22px;margin-bottom:8px;">📚</div>
                <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">RAG Knowledge Base</div>
                <div style="font-size:12px;color:#6a9450;line-height:1.5;">PARC Reports, FAO Guidelines, Punjab Agriculture Rules — all searchable.</div>
              </td>
              <td width="4%"></td>
              <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
                <div style="font-size:22px;margin-bottom:8px;">🌐</div>
                <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">Live Web Search</div>
                <div style="font-size:12px;color:#6a9450;line-height:1.5;">When the answer isn't in the docs, we search trusted Pakistani sources live.</div>
              </td>
            </tr>
            <tr><td colspan="3" height="12"></td></tr>
            <tr>
              <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
                <div style="font-size:22px;margin-bottom:8px;">⚡</div>
                <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">MCP Tools</div>
                <div style="font-size:12px;color:#6a9450;line-height:1.5;">Real-time weather, crop calendar, unit converter, market prices.</div>
              </td>
              <td width="4%"></td>
              <td style="background:#f0f7ec;border:1px solid #c8dab8;border-radius:10px;padding:16px 18px;width:48%;vertical-align:top;">
                <div style="font-size:22px;margin-bottom:8px;">📁</div>
                <div style="font-size:13px;font-weight:700;color:#1a3a0a;margin-bottom:4px;">Project Management</div>
                <div style="font-size:12px;color:#6a9450;line-height:1.5;">Organise your research into projects. Upload your own PDFs.</div>
              </td>
            </tr>
          </table>

          <!-- Privacy notice -->
          <div style="background:#fff8e8;border:1px solid #e0c070;border-radius:10px;padding:14px 18px;margin-bottom:24px;">
            <div style="font-size:13px;font-weight:700;color:#8a5800;margin-bottom:4px;">🔒 You have shared your account with AgriBot</div>
            <div style="font-size:12.5px;color:#6a4000;line-height:1.6;">
              This confirms that you have shared your account information (username and email) with AgriBot for the purpose of accessing agricultural knowledge services. We do not share your data with third parties. Your conversations are stored securely to enable conversation history. If you did not perform this action, please contact us immediately.
            </div>
          </div>

          <p style="color:#3a5020;font-size:14px;line-height:1.7;margin:0 0 24px;">
            You can start asking questions immediately. Try: <em style="color:#4a8a1e;">"What wheat diseases are common in Punjab?"</em> or <em style="color:#4a8a1e;">"Is tomorrow a good day for sowing in Lahore?"</em>
          </p>

          <!-- CTA -->
          <div style="text-align:center;">
            <a href="http://localhost:5173" style="display:inline-block;background:#4a8a1e;color:#ffffff;font-size:14px;font-weight:700;padding:13px 32px;border-radius:10px;text-decoration:none;letter-spacing:0.01em;">Open AgriBot →</a>
          </div>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f0f7ec;border-top:1px solid #c8dab8;padding:20px 40px;text-align:center;">
          <p style="color:#6a9450;font-size:11.5px;margin:0;line-height:1.6;">
            AgriBot · Agricultural Knowledge Assistant for Pakistan<br>
            © {year} AgriBot. Powered by Groq + ChromaDB + Tavily.<br>
            <span style="color:#aaa;">If you did not register for this account, please ignore this email.</span>
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_plain(username: str) -> str:
    return f"""You have shared your account with AgriBot, {username}!

This confirms your AgriBot account has been successfully created and you
have shared your account information (username and email) with AgriBot.

AgriBot is Pakistan's Agricultural Knowledge Assistant powered by:
- RAG knowledge base (PARC Reports, FAO Guidelines, Punjab Agriculture Rules)
- Live web search via Tavily
- MCP tools: weather, crop calendar, unit converter
- Project management: organise research, upload your own PDFs

PRIVACY NOTICE:
We do not share your data with third parties.
If you did not perform this action, please contact us immediately.

Start now at: http://localhost:5173

---
AgriBot · Agricultural Knowledge Assistant
If you did not register, please ignore this email.
"""


# ── Main function ─────────────────────────────────────────────────────────────

def mcp_send_welcome_email(username: str, email: str) -> dict:
    """
    MCP Tool: Send a welcome email to a newly registered AgriBot user.

    Called from auth_routes.py after successful registration.
    Never raises — always returns a result dict.

    Returns:
        {"status": "sent",    "to": email}
        {"status": "skipped", "reason": "..."}
        {"status": "error",   "error": "..."}
    """
    if not email or "@" not in email:
        return {"status": "skipped", "reason": "No valid email address provided"}

    if not _ENABLED:
        print(f"[MCP/email] Disabled (AGRIBOT_EMAIL_ENABLED != true). Would send to {email}")
        return {"status": "skipped", "reason": "Email sending disabled"}

    if not _FROM or not _PASS:
        print(
            "[MCP/email] AGRIBOT_EMAIL_FROM or AGRIBOT_EMAIL_PASSWORD not set.\n"
            "  Set them in your .env or terminal:\n"
            "    export AGRIBOT_EMAIL_FROM=youragribot@gmail.com\n"
            "    export AGRIBOT_EMAIL_PASSWORD='xxxx xxxx xxxx xxxx'"
        )
        return {"status": "skipped", "reason": "Email credentials not configured"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🌾 You have shared your account with AgriBot"
        msg["From"]    = f"AgriBot <{_FROM}>"
        msg["To"]      = email

        msg.attach(MIMEText(_build_plain(username), "plain"))
        msg.attach(MIMEText(_build_html(username),  "html"))

        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(_FROM, _PASS)
            server.sendmail(_FROM, [email], msg.as_string())

        print(f"[MCP/email] ✓ Welcome email sent → {email} (user: {username})")
        return {"status": "sent", "to": email}

    except smtplib.SMTPAuthenticationError:
        msg = "Gmail authentication failed. Make sure you're using an App Password, not your regular password."
        print(f"[MCP/email] ✗ {msg}")
        return {"status": "error", "error": msg}

    except Exception as e:
        print(f"[MCP/email] ✗ Failed: {e}\n{traceback.format_exc()}")
        return {"status": "error", "error": str(e)}
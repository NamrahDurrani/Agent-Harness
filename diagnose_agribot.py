"""
diagnose_agribot.py
====================
Run this from your project folder (same venv) to check exactly why:
  1. The welcome email isn't arriving
  2. Anything else is misconfigured

Usage:
    python diagnose_agribot.py
"""

import os
import sys

print("=" * 65)
print("AGRIBOT DIAGNOSTIC")
print("=" * 65)

# ── 1. Check mcp_email.py exists and imports ──────────────────────────────────
print("\n[1] Checking mcp_email.py...")
try:
    from mcp_email import mcp_send_welcome_email, _FROM, _PASS, _ENABLED
    print("  ✓ mcp_email.py imported successfully")
    print(f"  AGRIBOT_EMAIL_FROM     = {_FROM!r}")
    print(f"  AGRIBOT_EMAIL_PASSWORD = {'*' * len(_PASS) if _PASS else '(EMPTY!)'}")
    print(f"  AGRIBOT_EMAIL_ENABLED  = {_ENABLED}")

    if not _FROM:
        print("  ✗ PROBLEM: AGRIBOT_EMAIL_FROM is not set in this terminal session.")
    if not _PASS:
        print("  ✗ PROBLEM: AGRIBOT_EMAIL_PASSWORD is not set in this terminal session.")
    if not _ENABLED:
        print("  ✗ PROBLEM: AGRIBOT_EMAIL_ENABLED is 'false' — set it to 'true'.")

except ImportError as e:
    print(f"  ✗ Could not import mcp_email.py: {e}")
    print("  → Make sure mcp_email.py is in the SAME folder as api_server.py")
    sys.exit(1)

# ── 2. Live send test ──────────────────────────────────────────────────────────
if _FROM and _PASS and _ENABLED:
    print("\n[2] Attempting to send a real test email...")
    test_email = input("  Enter an email address to send a test to: ").strip()
    if test_email:
        result = mcp_send_welcome_email("diagnostic_test_user", test_email)
        print(f"  Result: {result}")
        if result.get("status") == "sent":
            print("  ✓ Email sent! Check your inbox AND spam folder.")
        elif result.get("status") == "error":
            print(f"  ✗ SMTP error: {result.get('error')}")
            if "Authentication" in str(result.get("error", "")):
                print("\n  This means Gmail rejected your login. Common causes:")
                print("  1. You used your REGULAR Gmail password instead of an App Password")
                print("  2. 2-Step Verification is not enabled on the Gmail account")
                print("  3. The App Password has spaces stripped incorrectly")
                print("\n  Fix: https://myaccount.google.com/apppasswords")
    else:
        print("  Skipped (no email entered)")
else:
    print("\n[2] Skipping send test — env vars not fully configured (see above)")

# ── 3. Check rag_pipeline.py PipelineResult structure ──────────────────────────
print("\n[3] Checking rag_pipeline.PipelineResult...")
try:
    from rag_pipeline import PipelineResult
    dummy = PipelineResult(answer="test", sources=[])
    print(f"  ✓ PipelineResult has .answer attribute: {hasattr(dummy, 'answer')}")
    print(f"  ✓ PipelineResult has .sources attribute: {hasattr(dummy, 'sources')}")
    print(f"  ✓ PipelineResult has .source_type attribute: {hasattr(dummy, 'source_type')}")
    print(f"  ✓ PipelineResult has .used_rag attribute: {hasattr(dummy, 'used_rag')}")
except Exception as e:
    print(f"  ✗ Could not import PipelineResult: {e}")

# ── 4. Environment variable summary ────────────────────────────────────────────
print("\n[4] All AgriBot-related environment variables in this terminal:")
for key in ["AGRIBOT_EMAIL_FROM", "AGRIBOT_EMAIL_PASSWORD", "AGRIBOT_EMAIL_ENABLED",
            "GROQ_API_KEY", "TAVILY_API_KEY", "SECRET_KEY"]:
    val = os.environ.get(key, "")
    display = "*" * min(len(val), 12) if val else "(NOT SET)"
    print(f"  {key:25s} = {display}")

print("\n" + "=" * 65)
print("IMPORTANT: env vars set with $env:VAR=\"value\" in PowerShell only")
print("last for THAT terminal session. If you closed and reopened the")
print("terminal before running api_server.py, the vars are gone.")
print("Run set_env.ps1 (or set them manually) in the SAME terminal")
print("where you then run: python api_server.py")
print("=" * 65)

# <#
# finetuning\baseline\run_until_target.ps1

# Auto-reruns build_eval_set.py until eval_set_v1.jsonl reaches the target
# question count, WITHOUT you having to manually relaunch it every time the
# script's own 60-call safety cap kicks in.

# It only stops early if it detects a REAL Groq problem (daily quota
# exhausted or an auth error) — the same markers build_eval_set.py itself
# checks for. In that case it prints a clear message and exits; just rerun
# this script later once your quota resets, and it will resume exactly
# where it left off (the underlying script is already resumable).

# Usage (run from your project root, e.g. agenti_rag\):
#     .\finetuning\baseline\run_until_target.ps1
#     .\finetuning\baseline\run_until_target.ps1 -Target 40 -MaxApiCallsPerRun 150
# #>

param(
    [int]$Target = 40,
    [int]$MaxApiCallsPerRun = 150,   # raised from the script's default of 60 — real limiter is your Groq quota, not this
    [int]$SleepSeconds = 15,         # brief pause between reruns, easy on the API
    [string]$EvalSetPath = "finetuning\data\eval_set_v1.jsonl"
)

function Get-QuestionCount {
    if (Test-Path $EvalSetPath) {
        return (Get-Content $EvalSetPath | Where-Object { $_.Trim() -ne "" } | Measure-Object -Line).Lines
    }
    return 0
}

Write-Host "=================================================="
Write-Host "AUTO-RESUME EVAL SET BUILDER"
Write-Host "Target: $Target questions | Cap per run: $MaxApiCallsPerRun API calls"
Write-Host "=================================================="

while ($true) {
    $count = Get-QuestionCount
    Write-Host "`n[LOOP] Current eval set size: $count / $Target"

    if ($count -ge $Target) {
        Write-Host "[LOOP] Target reached. Stopping. Freeze the file before doing anything else:"
        Write-Host "       Copy-Item `"$EvalSetPath`" `"$($EvalSetPath -replace '\.jsonl$','_FROZEN.jsonl')`""
        break
    }

    $output = & python finetuning\baseline\build_eval_set.py --max-api-calls $MaxApiCallsPerRun 2>&1 | Out-String
    Write-Host $output

    if ($output -match "Daily/account quota exhausted" -or $output -match "Authentication error") {
        Write-Host "`n[LOOP] Hit a REAL Groq limit (not the script's artificial cap) — stopping."
        Write-Host "[LOOP] Wait for the quota to reset, then just rerun this same script — it resumes automatically."
        break
    }

    $newCount = Get-QuestionCount
    if ($newCount -eq $count) {
        Write-Host "[LOOP] No new questions were added this pass (all rejected). Stopping to avoid burning calls in a loop with no progress."
        Write-Host "[LOOP] Check your KB topic buckets / verification prompt before rerunning."
        break
    }

    Write-Host "[LOOP] Sleeping $SleepSeconds seconds before next pass..."
    Start-Sleep -Seconds $SleepSeconds
}

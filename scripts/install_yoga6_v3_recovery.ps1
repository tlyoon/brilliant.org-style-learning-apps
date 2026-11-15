# Install a bounded, restart-safe BOSLA V3 recovery task for the OWNER'S Yoga 6.
# No credentials in the task. No model call during installation.
# Default behavior is a safe inspection; -Install explicitly registers it.
[CmdletBinding()]
param([switch]$Install,[switch]$Uninstall)
$ErrorActionPreference = 'Stop'
if ($Install -and $Uninstall) { throw 'Choose -Install or -Uninstall' }
if ($env:COMPUTERNAME -ine 'YOGA6') { throw 'V3_NATIVE_REVIEW_WRONG_WORKSTATION' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$authority = Join-Path $repo 'config\configure_project.toml'
if (-not (Test-Path -LiteralPath $authority)) { throw 'V3_NATIVE_REVIEW_HOST_CONFIG_UNAVAILABLE' }
$python = (Get-Command python.exe -ErrorAction Stop).Source
$worker = Join-Path $repo 'scripts\run_v3_yoga6_recovery_worker.py'
if (-not (Test-Path -LiteralPath $worker)) { throw 'V3_RECOVERY_WORKER_MISSING' }
$taskName = 'BoslaYoga6V3Recovery'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($Uninstall) {
    if ($existing) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false }
    Write-Output 'BOSLA_YOGA6_RECOVERY_TASK_UNREGISTERED'
    return
}
# Never overwrite a task of the same name with a different payload.
$argument = ('"' + $worker + '" --execute --allow-generated-text-transfer')
# Allow two sequential 20-minute SDK calls plus setup without task-killing a
# potentially accepted provider request before its checkpoint is persisted.
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 60) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
if ($existing) {
    $action = $existing.Actions | Select-Object -First 1
    if ($existing.Actions.Count -ne 1 -or
        $action.Execute -ne $python -or
        $action.Arguments -ne $argument) {
        throw 'BOSLA_RECOVERY_TASK_CONFLICT_REFUSED'
    }
    if ($Install) {
        # Idempotently repair settings without replacing task principal/action.
        Set-ScheduledTask -TaskName $taskName -Settings $settings | Out-Null
        Write-Output 'BOSLA_YOGA6_RECOVERY_TASK_SETTINGS_VERIFIED'
    }
    Write-Output 'BOSLA_YOGA6_RECOVERY_TASK_ALREADY_CONFIGURED'
    Get-ScheduledTaskInfo -TaskName $taskName | Select-Object NextRunTime, LastRunTime, LastTaskResult
    return
}
if (-not $Install) {
    Write-Output 'BOSLA_YOGA6_RECOVERY_TASK_NOT_INSTALLED'
    Write-Output 'Pass -Install to create one current-user, interactive, half-hourly task.'
    return
}
# The user account must be logged on, since the working checkout is in the
# owner's Google Drive and the credentials are in that user's LocalAppData.
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(30) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)
$action = New-ScheduledTaskAction -Execute $python -Argument $argument -WorkingDirectory $repo
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'BOSLA Yoga6 source-free Gemini diagnostic + at most one fresh V3 review per tick; immutable no-replay circuit' | Out-Null
Write-Output 'BOSLA_YOGA6_RECOVERY_TASK_REGISTERED'
Get-ScheduledTaskInfo -TaskName $taskName | Select-Object NextRunTime, LastRunTime, LastTaskResult

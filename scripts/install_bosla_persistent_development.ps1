# BSA279 owner-explicit 27 Nov 2026: NEW persistent Bosla development service.
# The retired BoslaYoga6V3Recovery 30-minute task stays absent.
# One new task includes BOTH logon + a 15-minute repeated daily trigger.
# Windows Task Scheduler starts runs independently of this ChatGPT session.
# Task has IgnoreNew (plus Python OS mutex), restart-on-failure,
# no public deployment, and executable academic acceptance safety gates.
[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$Remove,
    [switch]$Status,
    [switch]$RunNow
)
$ErrorActionPreference='Stop'
$taskName='BoslaPersistentDevelopment-Yoga6'
$legacy='BoslaYoga6V3Recovery'
if ($env:COMPUTERNAME -ine 'YOGA6') {
    throw 'BSA279_PERSISTENT_BOSLA_YOGA6_ONLY'
}
$repo=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python=Join-Path $repo '.venv\Scripts\python.exe'
$worker=Join-Path $repo 'scripts\bosla_persistent_development.py'
if (-not (Test-Path -LiteralPath $python)) {throw 'BSA279_EXACT_OWNER_PYTHON_MISSING'}
if (-not (Test-Path -LiteralPath $worker)) {throw 'BSA279_EXECUTABLE_DISPATCHER_MISSING'}
if (Get-ScheduledTask -TaskName $legacy -ErrorAction SilentlyContinue) {
    throw 'BSA279_RETIRED_LEGACY_TASK_PRESENT_DO_NOT_REINSTALL'
}
if ($Remove) {
    $prior=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($prior) {
        if ($prior.State -eq 'Running') {
            Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        }
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    }
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        throw 'BSA279_TASK_REMOVAL_NOT_CONFIRMED'
    }
    Write-Output 'BSA279_NEW_PERSISTENCE_TASK_UNINSTALLED_VERIFIED'
    exit 0
}
if ($Install) {
    # BSA307: module entry is stable even when new owner code imports
    # app_generator -> scripts before cycle() begins. The previous absolute
    # .py-file invocation failed with ModuleNotFoundError: scripts on Yoga6.
    $action=New-ScheduledTaskAction -Execute $python -Argument '-B -m scripts.bosla_persistent_development --once' -WorkingDirectory $repo
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    $logon=New-ScheduledTaskTrigger -AtLogOn -User $identity
    # ScheduledTasks -Daily has no mutable Repetition property on Yoga6.
    # Use the supported -Once repetition parameter set; an additional
    # logon trigger guarantees resume at sign-in. The ten-year repeat
    # horizon is bounded, not an unverified indefinite CIM mutation.
    $daily=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
    $settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartInterval (New-TimeSpan -Minutes 5) -RestartCount 3 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $principal=New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
    $registered=Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($logon,$daily) -Settings $settings -Principal $principal -Force
    if (-not $registered) {throw 'BSA279_NEW_SCHEDULER_NOT_REGISTERED'}
    Write-Output ('BSA279_PERSISTENCE_INSTALLED='+$registered.TaskName)
}
$task=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Output 'BSA279_PERSISTENCE_NOT_INSTALLED'
    exit 2
}
if ($RunNow) {
    Start-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 2
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
}
if ($Install -or $Status -or $RunNow) {
    $info=Get-ScheduledTaskInfo -TaskName $taskName
    $triggers=@($task.Triggers)
    if ($triggers.Count -lt 2) {
        throw 'BSA279_LOGON_AND_REPEATING_TRIGGERS_NOT_INSTALLED'
    }
    if ($task.Actions.Count -ne 1 -or
        $task.Actions[0].Execute -ine $python -or
        $task.Actions[0].Arguments -cne '-B -m scripts.bosla_persistent_development --once' -or
        $task.Actions[0].WorkingDirectory -ine $repo) {
        throw 'BSA279_SCHEDULED_ACTION_NOT_SOURCE_BOUND'
    }
    [pscustomobject]@{
        Status='BSA279_PERSISTENT_BOSLA_DEVELOPMENT_ENABLED'
        TaskName=$task.TaskName
        State=$task.State.ToString()
        TriggerCount=$triggers.Count
        Account=$task.Principal.UserId
        Program=$task.Actions[0].Execute
        Arguments=$task.Actions[0].Arguments
        LastRunTime=$info.LastRunTime
        NextRunTime=$info.NextRunTime
        LastTaskResult=$info.LastTaskResult
        LegacyTaskAbsent=$true
    } | ConvertTo-Json -Compress -Depth 5
}

# Retired BOSLA Yoga 6 scheduled-task installer.
# 2026-11-16 owner directive: remove the 30-minute task; do NOT recreate it.
# The normal, explicitly authorized CLI uses --auto-advance instead.
# This file deliberately retains ONLY inspection / uninstallation support.
[CmdletBinding()]
param([switch]$Install,[switch]$Uninstall)
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ine 'YOGA6') { throw 'V3_NATIVE_REVIEW_WRONG_WORKSTATION' }
if ($Install) {
    throw 'BOSLA_V3_SCHEDULING_RETIRED_USE_AUTO_ADVANCE'
}
$taskName = 'BoslaYoga6V3Recovery'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($Uninstall) {
    if ($existing) {
        if ($existing.State -eq 'Running') {
            Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        }
        Disable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    }
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        throw 'BOSLA_V3_SCHEDULE_REMOVAL_UNVERIFIED'
    }
    Write-Output 'BOSLA_V3_SCHEDULE_ABSENT_VERIFIED'
    return
}
if ($existing) {
    Write-Output 'BOSLA_V3_LEGACY_SCHEDULE_PRESENT_USE_UNINSTALL'
} else {
    Write-Output 'BOSLA_V3_SCHEDULE_ABSENT'
}
Write-Output 'Run the normal worker with explicit --auto-advance and permitted execution/transfer flags.'

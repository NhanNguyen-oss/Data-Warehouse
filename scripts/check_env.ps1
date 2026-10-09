# Stage S0 environment check for Windows. Run from the repository root:
#   powershell -ExecutionPolicy Bypass -File scripts\check_env.ps1
# Paste the output into PROJECT_PLAN.md (section 12) so the next agent knows the machine.

$ErrorActionPreference = "Continue"

function Show-Command($label, $command, $arguments) {
    $found = Get-Command $command -ErrorAction SilentlyContinue
    if (-not $found) {
        "{0,-16} NOT FOUND" -f $label
        return
    }
    $output = (& $command @arguments 2>&1 | Select-Object -First 1) -join " "
    "{0,-16} {1}" -f $label, $output
}

"== System =="
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
"{0,-16} {1} (build {2})" -f "Windows", $os.Caption, $os.BuildNumber
"{0,-16} {1:N1} GB" -f "RAM", ($cs.TotalPhysicalMemory / 1GB)
$drive = Get-PSDrive -Name (Get-Location).Drive.Name
"{0,-16} {1:N1} GB free" -f "Disk (repo)", ($drive.Free / 1GB)
$virt = (Get-CimInstance Win32_Processor | Select-Object -First 1).VirtualizationFirmwareEnabled
"{0,-16} {1}" -f "Virtualization", $virt

"`n== Tools =="
Show-Command "git" "git" @("--version")
Show-Command "python" "python" @("--version")
Show-Command "py launcher" "py" @("--version")
Show-Command "docker" "docker" @("version", "--format", "{{.Server.Version}}")
Show-Command "docker compose" "docker" @("compose", "version")
Show-Command "psql" "psql" @("--version")
Show-Command "code (VS Code)" "code" @("--version")

"`n== WSL =="
$wsl = Get-Command wsl -ErrorAction SilentlyContinue
if ($wsl) { wsl --status 2>&1 } else { "wsl NOT FOUND" }

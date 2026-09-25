# Adds Studio to Windows startup + a desktop shortcut to http://localhost:8787
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyw = (Get-Command pythonw.exe).Source
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("$([Environment]::GetFolderPath('Startup'))\ParentWiseStudio.lnk")
$s.TargetPath = $pyw; $s.Arguments = "studio.py --no-browser"; $s.WorkingDirectory = $root; $s.WindowStyle = 7; $s.Save()
$d = $ws.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\Parent Wise Studio.url")
$d.TargetPath = "http://localhost:8787"; $d.Save()
Write-Host "Startup + desktop shortcuts created."

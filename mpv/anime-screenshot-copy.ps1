param(
    [Parameter(Mandatory = $true)]
    [string]$ImagePath
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$source = [System.Drawing.Image]::FromFile($ImagePath)
$bitmap = $null

try {
    $bitmap = New-Object System.Drawing.Bitmap $source

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            [System.Windows.Forms.Clipboard]::SetDataObject($bitmap, $true)
            exit 0
        } catch {
            if ($attempt -eq 5) {
                throw
            }
            Start-Sleep -Milliseconds 100
        }
    }
} finally {
    if ($source) {
        $source.Dispose()
    }
}

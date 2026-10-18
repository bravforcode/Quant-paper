[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath,
    [Parameter(Mandatory = $true)]
    [string]$RootPath
)

$ErrorActionPreference = 'Stop'
# Resolve both paths against the PowerShell location: .NET GetFullPath uses the
# process directory, which differs after Set-Location/Push-Location. Path.Combine
# returns an absolute second argument unchanged.
$base = (Get-Location).ProviderPath
$root = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($base, $RootPath))
$manifest = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($base, $ManifestPath))
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
    throw "Manifest root directory does not exist: $root"
}
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw "Manifest file does not exist: $manifest"
}

$rootPrefix = $root.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$lineNumber = 0
$verified = 0
foreach ($line in [System.IO.File]::ReadAllLines($manifest)) {
    $lineNumber++
    $match = [System.Text.RegularExpressions.Regex]::Match(
        $line,
        '^(?<hash>[0-9A-Fa-f]{64})  (?<path>.+)$'
    )
    if (-not $match.Success) {
        throw "Malformed manifest line $lineNumber; expected 64 hex digits, two spaces, and a path."
    }

    $relativePath = $match.Groups['path'].Value
    if ([System.IO.Path]::IsPathRooted($relativePath)) {
        throw "Manifest path must be relative (line $lineNumber): $relativePath"
    }
    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $root $relativePath))
    if (-not $fullPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Manifest path escapes its declared root (line $lineNumber): $relativePath"
    }
    if (-not $seen.Add($fullPath)) {
        throw "Duplicate manifest path on line ${lineNumber}: $relativePath"
    }
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        throw "Manifest file is missing (line $lineNumber): $relativePath"
    }

    $actual = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash
    if ($actual -ine $match.Groups['hash'].Value) {
        throw "SHA-256 mismatch on line ${lineNumber}: $relativePath"
    }
    $verified++
}

if ($verified -eq 0) {
    throw 'Manifest contains no file entries.'
}
Write-Output "Verified $verified manifest entries under $root."

param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$OutputDocx,
    [Parameter(Mandatory = $true)][string]$OutputPdf
)

$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$docxPath = [System.IO.Path]::GetFullPath($OutputDocx)
$pdfPath = [System.IO.Path]::GetFullPath($OutputPdf)
foreach ($target in @($docxPath, $pdfPath)) {
    if (Test-Path -LiteralPath $target) {
        throw "Output already exists; choose a new revision: $target"
    }
}

$sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ('cpiv-review-' + [guid]::NewGuid())
[void](New-Item -ItemType Directory -Path $tempDir)
$tempDocx = Join-Path $tempDir 'manuscript.docx'
Copy-Item -LiteralPath $sourcePath -Destination $tempDocx

$wordApp = $null
$document = $null
$details = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    if ($wordApp.Visible -or $wordApp.Documents.Count -ne 0) {
        throw 'Refusing to automate a visible Word session or one with open documents.'
    }
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordApp.AutomationSecurity = 3
    $document = $wordApp.Documents.Open($tempDocx, $false, $false)
    if ($document.ReadOnly) {
        throw 'Task-scoped working copy unexpectedly opened read-only.'
    }

    foreach ($section in $document.Sections) {
        $section.PageSetup.PaperSize = 7 # wdPaperA4
        $footer = $section.Footers.Item(1) # wdHeaderFooterPrimary
        if ($footer.PageNumbers.Count -eq 0) {
            $null = $footer.PageNumbers.Add(1, $true) # centered, include first page
        }
    }
    foreach ($tableOfContents in $document.TablesOfContents) {
        $null = $tableOfContents.Update()
    }
    $document.Repaginate()
    $null = $document.Fields.Update()
    $document.Save()
    $details = [ordered]@{
        status = 'rendered_by_microsoft_word'
        source = $sourcePath
        source_sha256 = $sourceHash
        output_docx = $docxPath
        output_pdf = $pdfPath
        pages = $document.ComputeStatistics(2)
        tables = $document.Tables.Count
        equations = $document.OMaths.Count
        inline_shapes = $document.InlineShapes.Count
        page_width_pt = $document.Sections.Item(1).PageSetup.PageWidth
        page_height_pt = $document.Sections.Item(1).PageSetup.PageHeight
    }
    $document.ExportAsFixedFormat($pdfPath, 17)
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $wordApp) {
        if ($wordApp.Documents.Count -eq 0 -and -not $wordApp.Visible) {
            $wordApp.Quit()
        }
    }
}

Copy-Item -LiteralPath $tempDocx -Destination $docxPath
if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne $sourceHash) {
    throw 'Source changed during export.'
}
$details.output_docx_sha256 = (Get-FileHash -LiteralPath $docxPath -Algorithm SHA256).Hash
$details.output_pdf_sha256 = (Get-FileHash -LiteralPath $pdfPath -Algorithm SHA256).Hash
$details | ConvertTo-Json -Depth 3

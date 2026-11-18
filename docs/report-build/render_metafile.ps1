$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$inputReport=(Get-ChildItem (Split-Path $PSScriptRoot -Parent) -Filter '*-UML*.docx' | Where-Object { -not $_.Name.StartsWith('~$') } | Select-Object -First 1).FullName
$renderDir=Join-Path $PSScriptRoot 'render'
New-Item -ItemType Directory -Force $renderDir | Out-Null
$renderWord=New-Object -ComObject Word.Application
$renderWord.Visible=$false
$renderWord.DisplayAlerts=0
$renderWord.Options.UpdateFieldsAtPrint=$false
$renderWord.Options.UpdateLinksAtPrint=$false
try {
    $renderDoc=$renderWord.Documents.Open($inputReport,$false,$false)
    foreach ($fieldItem in $renderDoc.Fields) {
        if ($fieldItem.Type -eq 12) { $fieldItem.Update() | Out-Null }
    }
    foreach ($fieldItem in $renderDoc.Fields) {
        if ($fieldItem.Type -eq 3) { $fieldItem.Update() | Out-Null }
    }
    foreach ($toc in $renderDoc.TablesOfContents) { $toc.Update() }
    $renderDoc.ActiveWindow.View.Type=3
    $renderDoc.ActiveWindow.View.Zoom.Percentage=100
    $renderDoc.Repaginate()
    foreach ($toc in $renderDoc.TablesOfContents) { $toc.UpdatePageNumbers() }
    $renderDoc.Save()
    $renderPages=$renderDoc.ActiveWindow.Panes.Item(1).Pages
    Write-Output ('Native pages: '+$renderPages.Count)
    for ($pageIndex=1; $pageIndex -le $renderPages.Count; $pageIndex++) {
        $pageBytes=[byte[]]$renderPages.Item($pageIndex).EnhMetaFileBits
        $stream=New-Object System.IO.MemoryStream(,$pageBytes)
        $meta=New-Object System.Drawing.Imaging.Metafile($stream)
        $bitmap=New-Object System.Drawing.Bitmap([int]($meta.Width/4),[int]($meta.Height/4))
        $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
        $graphics.Clear([System.Drawing.Color]::White)
        $graphics.DrawImage($meta,0,0,$bitmap.Width,$bitmap.Height)
        $bitmap.Save((Join-Path $renderDir ('page-'+$pageIndex+'.png')),[System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose(); $bitmap.Dispose(); $meta.Dispose(); $stream.Dispose()
        if ($pageIndex % 10 -eq 0) { Write-Output ('Rendered '+$pageIndex) }
    }
    Write-Output 'All page images rendered'
    $renderDoc.Close(0)
} finally { $renderWord.Quit() }

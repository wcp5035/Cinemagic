param(
    [Parameter(Mandatory = $true)]
    [string]$Owner,

    [Parameter(Mandatory = $true)]
    [string]$Repo,

    [Parameter(Mandatory = $true)]
    [string]$Token,

    [string]$Tag = "v1.1.0",
    [string]$ReleaseName = "Cinemagic v1.1.0 Windows",
    [string]$SourceDir = "$PSScriptRoot\..\dist\Cinemagic",
    [string]$ZipPath = "$PSScriptRoot\..\dist\Cinemagic-Windows-x64.zip"
)

$ErrorActionPreference = "Stop"

function Invoke-GitHubApi {
    param(
        [string]$Method,
        [string]$Uri,
        [object]$Body = $null
    )

    $headers = @{
        Authorization = "Bearer $Token"
        Accept        = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
        "User-Agent"  = "Cinemagic-Release-Uploader"
    }

    $params = @{
        Method  = $Method
        Uri     = $Uri
        Headers = $headers
    }
    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 8)
        $params.ContentType = "application/json"
    }
    return Invoke-RestMethod @params
}

if (-not (Test-Path $SourceDir)) {
    throw "Source directory not found: $SourceDir"
}

Write-Host "Preparing release zip..."
$staging = Join-Path $env:TEMP ("cinemagic-release-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $staging | Out-Null
try {
    Copy-Item -Path $SourceDir -Destination (Join-Path $staging "Cinemagic") -Recurse
  $exampleConfig = Join-Path $PSScriptRoot "..\config.example.toml"
  $targetConfig = Join-Path $staging "Cinemagic\config.toml"
  if (Test-Path $exampleConfig) {
    Copy-Item $exampleConfig $targetConfig -Force
    Write-Host "Replaced config.toml with config.example.toml (no API keys)."
  }
  if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
  }
  Compress-Archive -Path (Join-Path $staging "Cinemagic") -DestinationPath $ZipPath -CompressionLevel Optimal
}
finally {
  if (Test-Path $staging) {
    Remove-Item $staging -Recurse -Force
  }
}

$zipSizeMb = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
Write-Host "Created zip: $ZipPath ($zipSizeMb MB)"

$releaseBody = @"
## Cinemagic Windows 便携版

1. 下载并解压 `Cinemagic-Windows-x64.zip`
2. 进入 `Cinemagic` 文件夹
3. 将 `config.example.toml` 复制为 `config.toml` 并填写 API Key
4. 双击 `Cinemagic.exe` 启动

默认地址：
- Web UI: http://127.0.0.1:8501
- API 文档: http://127.0.0.1:8080/docs
"@

Write-Host "Creating GitHub release $Tag on $Owner/$Repo ..."
try {
  $release = Invoke-GitHubApi -Method Post -Uri "https://api.github.com/repos/$Owner/$Repo/releases" -Body @{
    tag_name   = $Tag
    name       = $ReleaseName
    body       = $releaseBody
    draft      = $false
    prerelease = $false
  }
}
catch {
  if ($_.Exception.Message -match "422|already_exists") {
    Write-Host "Release already exists, fetching existing release..."
    $releases = Invoke-GitHubApi -Method Get -Uri "https://api.github.com/repos/$Owner/$Repo/releases/tags/$Tag"
    $release = $releases
  }
  else {
    throw
  }
}

Write-Host "Uploading asset..."
$uploadUrl = "https://uploads.github.com/repos/$Owner/$Repo/releases/$($release.id)/assets?name=$(Split-Path $ZipPath -Leaf)"
$headers = @{
  Authorization = "Bearer $Token"
  Accept        = "application/vnd.github+json"
  "X-GitHub-Api-Version" = "2022-11-28"
  "Content-Type" = "application/zip"
  "User-Agent"  = "Cinemagic-Release-Uploader"
}
$bytes = [System.IO.File]::ReadAllBytes($ZipPath)
$response = Invoke-RestMethod -Method Post -Uri $uploadUrl -Headers $headers -Body $bytes
Write-Host "Upload complete!"
Write-Host "Release URL: $($release.html_url)"
Write-Host "Download URL: $($response.browser_download_url)"

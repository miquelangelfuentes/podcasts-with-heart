"""Safe update helper for Podcasts with Heart Windows releases.

Only published GitHub releases are installable, and the running application
must exit before executable replacement starts.
"""

import os
import re
import stat
import zipfile
from pathlib import PurePosixPath


_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = _VERSION_RE.fullmatch(str(value).strip())
    if not match:
        raise ValueError(f"Versió de release incorrecta: {value!r}")
    return tuple(int(item) for item in match.groups())


def is_newer_release(installed_version: str, remote_tag: str) -> bool:
    return parse_version(remote_tag) > parse_version(installed_version)


def get_windows_asset(release: dict) -> dict:
    """Return only the release-matched Windows ZIP, not other assets."""
    version = parse_version(release.get("tag_name", ""))
    expected = "PodcastsWithHeart-v{}.{}.{}-Windows.zip".format(*version)
    for asset in release.get("assets", []):
        if asset.get("name") == expected and asset.get("browser_download_url", "").startswith(
            "https://github.com/miquelangelfuentes/podcasts-with-heart/releases/download/"
        ):
            return asset
    raise ValueError(f"The release does not include the official Windows package ({expected}).")


def extract_windows_release(zip_path: str, destination: str) -> str:
    """Validate package structure and reject unsafe archive paths."""
    with zipfile.ZipFile(zip_path) as archive:
        names = {entry.filename for entry in archive.infolist()}
        required = {
            "PodcastsWithHeart/PodcastsWithHeart.exe",
        }
        missing = required - names
        if missing:
            raise ValueError("The Windows package is incomplete: " + ", ".join(sorted(missing)))

        for entry in archive.infolist():
            normalized = entry.filename.replace("\\", "/")
            parts = PurePosixPath(normalized).parts
            mode = (entry.external_attr >> 16) & 0xFFFF
            if (
                normalized != entry.filename
                or not parts
                or parts[0] != "PodcastsWithHeart"
                or any(part in (".", "..") for part in parts)
                or normalized.startswith("/")
                or ":" in normalized
                or stat.S_ISLNK(mode)
            ):
                raise ValueError(f"Unsafe path in update ZIP: {entry.filename!r}")
        archive.extractall(destination)

    root = os.path.join(destination, "PodcastsWithHeart")
    if not os.path.isfile(os.path.join(root, "PodcastsWithHeart.exe")):
        raise ValueError("The executable is missing after extraction.")
    return root


def _ps_literal(path: str) -> str:
    """Escape apostrophes in PowerShell literals, including Windows user paths."""
    return "'" + str(path).replace("'", "''") + "'"


def make_windows_update_script(
    source_dir: str,
    install_dir: str,
    exe_path: str,
    parent_pid: int,
    version: str,
    staging_dir: str,
) -> str:
    """Generate an external helper that waits for exit and verifies the copy."""
    parse_version(version)
    for path in (source_dir, install_dir, exe_path, staging_dir):
        if not os.path.isabs(path):
            raise ValueError(f"Update paths must be absolute: {path!r}")
    if not parent_pid or int(parent_pid) < 1:
        raise ValueError("Invalid parent process ID.")

    src = _ps_literal(source_dir)
    dst = _ps_literal(install_dir)
    exe = _ps_literal(exe_path)
    stage = _ps_literal(staging_dir)
    log_name = _ps_literal(f"PodcastsWithHeart-update-v{'.'.join(map(str, parse_version(version)))}.log")
    return f"""$ErrorActionPreference = 'Stop'
$SourceDir = {src}
$TargetDir = {dst}
$TargetExe = {exe}
$StageDir = {stage}
$ParentPid = {int(parent_pid)}
$LogPath = Join-Path $env:TEMP {log_name}
try {{
    Add-Content -LiteralPath $LogPath -Value "Starting update {version}."
    $limit = (Get-Date).AddSeconds(120)
    while (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) {{
        if ((Get-Date) -gt $limit) {{
            throw "The previous application is still running. Close it and try again."
        }}
        Start-Sleep -Milliseconds 500
    }}
    Start-Sleep -Milliseconds 750
    if (-not (Test-Path -LiteralPath (Join-Path $SourceDir 'PodcastsWithHeart.exe'))) {{
        throw "The new executable is missing."
    }}
    # /E preserves user files; /XD leaves existing voice models untouched.
    # /IS /IT forces replacement of app files regardless of timestamp.
    & robocopy.exe $SourceDir $TargetDir /E /IS /IT /R:6 /W:2 /COPY:DAT /DCOPY:DA /XD models .venv /NP /NFL /NDL /NJH /NJS
    $copyCode = $LASTEXITCODE
    Add-Content -LiteralPath $LogPath -Value "Robocopy exit code: $copyCode"
    if ($copyCode -ge 8) {{
        throw "File copy failed (robocopy: $copyCode)."
    }}
    # Copy newly introduced voice models without overwriting models already stored.
    foreach ($ModelFolder in @('models', '_internal\\models')) {{
        $ModelSource = Join-Path $SourceDir $ModelFolder
        $ModelTarget = Join-Path $TargetDir $ModelFolder
        if (Test-Path -LiteralPath $ModelSource) {{
            & robocopy.exe $ModelSource $ModelTarget /E /XC /XN /XO /R:3 /W:1 /NP /NFL /NDL /NJH /NJS
            if ($LASTEXITCODE -ge 8) {{
                throw "Copying additional voice models failed."
            }}
        }}
    }}
    if (-not (Test-Path -LiteralPath $TargetExe)) {{
        throw "The updated executable is missing."
    }}
    $newHash = (Get-FileHash -LiteralPath (Join-Path $SourceDir 'PodcastsWithHeart.exe') -Algorithm SHA256).Hash
    $installedHash = (Get-FileHash -LiteralPath $TargetExe -Algorithm SHA256).Hash
    if ($newHash -ne $installedHash) {{
        throw "Executable integrity check failed."
    }}
    Add-Content -LiteralPath $LogPath -Value 'Copy completed and verified.'
    Start-Process -FilePath $TargetExe -WorkingDirectory $TargetDir
    Remove-Item -LiteralPath $StageDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
}} catch {{
    $message = $_.Exception.Message
    Add-Content -LiteralPath $LogPath -Value ("ERROR: " + $message)
    try {{
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            "Could not complete the update: " + $message + "\nSee log: " + $LogPath,
            'Podcasts with Heart update error',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
    }} catch {{}}
    exit 1
}}
"""

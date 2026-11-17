# Podcasts with Heart v1.0.2

## New: one-click updates from GitHub Releases

The **Check Version** dialog now checks the latest **published release** of this repository rather than the latest source-code commit. When a newer Windows package is available, it displays **Update application** and offers to download and install that exact version.

The updater:

- Compares semantic version numbers and ignores unrelated commits.
- Downloads the version-matched `PodcastsWithHeart-vX.Y.Z-Windows.zip` asset from the official repository.
- Validates the ZIP structure before installation and rejects unsafe archive paths.
- Waits until Podcasts with Heart is closed before replacing the application binaries.
- Checks the file-copy result and verifies the installed executable against the downloaded executable using SHA-256.
- Keeps existing voice models and can add newly bundled voice files without replacing models already present.
- Restarts the application after successful installation and writes an error log if installation fails.

## Upgrading from v1.0.1

**The old v1.0.1 has no automatic update/install button.** Download the new Windows ZIP once from this release, close the application, and replace the contents of the previous `PodcastsWithHeart` folder with the new package contents. Do not delete the existing `models` or `_internal/models` folders before copying; back them up if you have downloaded additional voice models.

After installing v1.0.2, future updates will use the new in-app **Update application** button when a newer release is published.

## Validation

The Windows CI checks release selection, ZIP validation, PowerShell helper syntax, the application test suite, and the packaged executable. A full real-device install/restart test is still recommended before considering every Windows configuration verified.

**Code signing:** the Windows executable is not yet signed by SignPath.

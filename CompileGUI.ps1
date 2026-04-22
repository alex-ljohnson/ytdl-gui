.\\.venv\\Scripts\\Activate.ps1
$ErrorActionPreference = 'Stop'
Write-Output "Syncing versions..."
python scripts/sync_versions.py
Write-Output "Removing previous build folder..."
if (Test-Path .\\dist\\DownloaderGUI) {Remove-Item .\\dist\\DownloaderGUI -Recurse -Force}
if (Test-Path .\\build\\DownloaderGUI) {Remove-Item .\\build\\DownloaderGUI -Recurse -Force}
pyinstaller.exe --name "DownloaderGUI" --version-file "..\\GrabVersion.py" --specpath ".\\build" --console -i '..\Resources\YTDLv2_256.ico' `
--hidden-import 'yt_dlp_ejs' --hidden-import 'spotipy' --hidden-import 'validators' --hidden-import 'mutagen' `
--add-data '../README.md;.' --add-data '../LICENSE;.' `
--add-data '../modules/extensions;modules/extensions' `
--add-data '../Info;Info' --add-data '../Resources;Resources' --add-data '../Logs;Logs' `
--add-data '../tksvg0.7;tksvg0.7' --add-data '../AtomicParsleyWindows;AtomicParsleyWindows' --add-data '../awthemes-10.3.0;awthemes-10.3.0' `
--add-data '../ffmpeg-7.1-essentials_build;ffmpeg-7.1-essentials_build' `
--add-data '../quickjs;quickjs' `
.\__main__.py
exit

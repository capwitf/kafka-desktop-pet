$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv-build\Scripts\python.exe")) {
    python -m venv .venv-build
}

.\.venv-build\Scripts\python.exe -m pip install --upgrade pip
.\.venv-build\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-build\Scripts\python.exe process_sprites.py --sprite tu.png --output-dir assets/frames --preview assets/frames_preview.png

.\.venv-build\Scripts\python.exe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name ZhuocDesktopPet `
    --add-data "assets;assets" `
    desktop_pet.py

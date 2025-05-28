# LM Studio API Client Web Version - PowerShell Install Script
# ================================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "LM Studio API Client Web Version - Install Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Python バージョン確認
Write-Host "[1/6] Pythonのバージョンを確認中..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Pythonがインストールされていません。" -ForegroundColor Red
    Write-Host "https://www.python.org/downloads/ からPythonをインストールしてください。" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

# 2. 古い仮想環境削除
Write-Host "[2/6] 古い仮想環境を削除中..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv"
    Write-Host "[OK] 古い仮想環境を削除しました。" -ForegroundColor Green
} else {
    Write-Host "[OK] 削除する仮想環境はありませんでした。" -ForegroundColor Green
}

# 3. 新しい仮想環境作成
Write-Host "[3/6] 新しい仮想環境を作成中..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 仮想環境の作成に失敗しました。" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}
Write-Host "[OK] 仮想環境を作成しました。" -ForegroundColor Green

# 4. 仮想環境アクティベート
Write-Host "[4/6] 仮想環境をアクティベート中..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 仮想環境のアクティベートに失敗しました。" -ForegroundColor Red
    Write-Host "PowerShellの実行ポリシーが制限されている可能性があります。" -ForegroundColor Red
    Write-Host "以下のコマンドを管理者権限で実行してください:" -ForegroundColor Yellow
    Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Enterキーを押して終了"
    exit 1
}
Write-Host "[OK] 仮想環境をアクティベートしました。" -ForegroundColor Green

# 5. 必要なディレクトリ作成
Write-Host "[5/6] 必要なディレクトリを作成中..." -ForegroundColor Yellow
if (!(Test-Path "static")) { New-Item -ItemType Directory -Name "static" | Out-Null }
if (!(Test-Path "templates")) { New-Item -ItemType Directory -Name "templates" | Out-Null }
Write-Host "[OK] ディレクトリを確認しました。" -ForegroundColor Green

# 6. 依存関係インストール
Write-Host "[6/6] 依存関係をインストール中..." -ForegroundColor Yellow
Write-Host "pipをアップグレード中..." -ForegroundColor Blue
python -m pip install --upgrade pip | Out-Null

Write-Host "Flaskとrequestsをインストール中..." -ForegroundColor Blue
pip install flask==2.3.3 requests==2.31.0

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] ライブラリのインストールに失敗しました。" -ForegroundColor Red
    Write-Host "ネットワーク接続を確認してから再実行してください。" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "インストールが完了しました！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

Write-Host "インストールされたパッケージ:" -ForegroundColor Cyan
pip list | Select-String -Pattern "flask|requests" | ForEach-Object { Write-Host $_ -ForegroundColor White }

Write-Host ""
Write-Host "Webアプリケーションを起動するには:" -ForegroundColor Cyan
Write-Host "  .\run_web.ps1" -ForegroundColor White
Write-Host ""
Write-Host "または、以下のコマンドを手動で実行:" -ForegroundColor Cyan
Write-Host "  1. .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. python web_app.py" -ForegroundColor White
Write-Host ""

Read-Host "Enterキーを押して終了" 
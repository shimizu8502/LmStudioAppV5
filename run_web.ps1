# LM Studio API Client Web Version - PowerShell Run Script
# ==========================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "LM Studio API Client (Web Version)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. 必要なディレクトリ確認
Write-Host "[1/4] 必要なディレクトリを確認中..." -ForegroundColor Yellow
if (!(Test-Path "static")) { New-Item -ItemType Directory -Name "static" | Out-Null }
if (!(Test-Path "templates")) { New-Item -ItemType Directory -Name "templates" | Out-Null }
Write-Host "[OK] ディレクトリを確認しました。" -ForegroundColor Green

# 2. 仮想環境確認
Write-Host "[2/4] 仮想環境を確認中..." -ForegroundColor Yellow
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] 仮想環境が見つかりません。" -ForegroundColor Red
    Write-Host "install_web.bat または install_web.ps1 を先に実行してください。" -ForegroundColor Red
    Write-Host ""
    Read-Host "Enterキーを押して終了"
    exit 1
}
Write-Host "[OK] 仮想環境が見つかりました。" -ForegroundColor Green

# 3. 仮想環境アクティベート
Write-Host "[3/4] 仮想環境をアクティベート中..." -ForegroundColor Yellow
try {
    & "venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Activation failed"
    }
    Write-Host "[OK] 仮想環境をアクティベートしました。" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 仮想環境のアクティベートに失敗しました。" -ForegroundColor Red
    Write-Host "PowerShellの実行ポリシーが制限されている可能性があります。" -ForegroundColor Red
    Write-Host ""
    Write-Host "解決方法:" -ForegroundColor Yellow
    Write-Host "1. PowerShellを管理者権限で開く" -ForegroundColor White
    Write-Host "2. 以下のコマンドを実行:" -ForegroundColor White
    Write-Host "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
    Write-Host "3. このスクリプトを再実行" -ForegroundColor White
    Write-Host ""
    Read-Host "Enterキーを押して終了"
    exit 1
}

# 4. Webサーバー起動
Write-Host "[4/4] Webサーバーを起動中..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "サーバーが起動しました！" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# ネットワーク情報を表示
Write-Host "アクセスURL:" -ForegroundColor Cyan
Write-Host "  ローカル: http://localhost:8000" -ForegroundColor White
Write-Host "  ネットワーク: http://0.0.0.0:8000" -ForegroundColor White

# IPアドレスを取得して表示
try {
    $localIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*" } | Select-Object -ExpandProperty IPAddress
    if ($localIPs) {
        Write-Host ""
        Write-Host "ネットワークからのアクセス:" -ForegroundColor Cyan
        foreach ($ip in $localIPs) {
            Write-Host "  http://${ip}:8000" -ForegroundColor White
        }
    }
} catch {
    # IPアドレス取得に失敗した場合は無視
}

Write-Host ""
Write-Host "ブラウザで上記URLにアクセスしてください。" -ForegroundColor Yellow
Write-Host "終了するには Ctrl+C を押してください。" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Pythonアプリケーション実行
python web_app.py

# 終了処理
Write-Host ""
if ($LASTEXITCODE -ne 0) {
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "[ERROR] アプリケーションでエラーが発生しました" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "考えられる原因:" -ForegroundColor Yellow
    Write-Host "  1. Flaskがインストールされていない" -ForegroundColor White
    Write-Host "  2. web_app.pyファイルに問題がある" -ForegroundColor White
    Write-Host "  3. ポート8000が既に使用されている" -ForegroundColor White
    Write-Host "  4. LM Studio APIサーバーが起動していない" -ForegroundColor White
    Write-Host ""
    Write-Host "解決方法:" -ForegroundColor Yellow
    Write-Host "  1. install_web.ps1 を再実行してください" -ForegroundColor White
    Write-Host "  2. LM Studio でAPIサーバーを起動してください" -ForegroundColor White
    Write-Host "  3. 他のアプリケーションがポート8000を使用していないか確認" -ForegroundColor White
    Write-Host "  4. エラーメッセージを確認してください" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "サーバーが正常に終了しました" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
}

Read-Host "Enterキーを押して終了" 
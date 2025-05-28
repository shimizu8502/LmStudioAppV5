@echo off
chcp 65001
cls
echo ================================================
echo LM Studio API Client Web Version - Install Script
echo ================================================
echo.

echo [1/6] Pythonのバージョンを確認中...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Pythonがインストールされていません。
    echo https://www.python.org/downloads/ からPythonをインストールしてください。
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Pythonが見つかりました。
echo.

echo [2/6] 古い仮想環境を削除中...
if exist venv (
    rmdir /s /q venv
    echo [OK] 古い仮想環境venvを削除しました。
)
if exist venv_new (
    rmdir /s /q venv_new
    echo [OK] 古い仮想環境venv_newを削除しました。
)

echo [3/6] 新しい仮想環境を作成中...
python -m venv venv_new
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境の作成に失敗しました。
    pause
    exit /b 1
)
echo [OK] 仮想環境を作成しました。

echo [4/6] 仮想環境をアクティベート中...
call venv_new\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境のアクティベートに失敗しました。
    pause
    exit /b 1
)
echo [OK] 仮想環境をアクティベートしました。

echo [5/6] 必要なディレクトリを作成中...
if not exist static mkdir static
if not exist templates mkdir templates
echo [OK] ディレクトリを確認しました。

echo [6/6] 依存関係をインストール中...
echo pipをアップグレード中...
python -m pip install --upgrade pip

echo Flaskとrequests、pyperclipをインストール中...
pip install flask==2.3.3 requests==2.31.0 pyperclip==1.8.2

if %errorlevel% neq 0 (
    echo [ERROR] ライブラリのインストールに失敗しました。
    echo ネットワーク接続を確認してから再実行してください。
    pause
    exit /b 1
)

echo.
echo ================================================
echo インストールが完了しました！
echo ================================================
echo.
echo インストールされたパッケージ:
pip list | findstr -i "flask requests"
echo.
echo Webアプリケーションを起動するには:
echo   run_web.bat をダブルクリックしてください
echo.
echo または、以下のコマンドを手動で実行:
echo   1. venv_new\Scripts\activate.bat
echo   2. python web_app.py
echo.
pause 
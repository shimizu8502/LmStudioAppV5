@echo off
echo ========================================
echo LM Studio Web アプリケーション（デバッグ版）
echo ========================================

REM 仮想環境をアクティベート
if exist "venv\Scripts\activate.bat" (
    echo 🔧 仮想環境をアクティベート中...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ 仮想環境が見つかりません。先にinstall_web.batを実行してください。
    pause
    exit /b 1
)

REM デバッグモードを有効にする環境変数を設定
set FLASK_DEBUG=true

echo 🚀 デバッグモードでWebアプリケーションを起動中...
echo 📝 デバッグ機能:
echo   - 自動リロード
echo   - 詳細なエラー情報
echo   - デバッガー機能
echo.
echo 🌐 ブラウザで http://localhost:8000 にアクセスしてください
echo 🛑 終了するには Ctrl+C を押してください
echo.

python web_app.py

echo.
echo ✅ アプリケーションが終了しました
pause 
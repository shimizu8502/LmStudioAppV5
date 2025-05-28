@echo off
chcp 65001
cls
echo ============================================
echo LM Studio API Client (Web Version)
echo ============================================
echo.

echo [1/4] 必要なディレクトリを確認中...
if not exist static mkdir static
if not exist templates mkdir templates
echo [OK] ディレクトリを確認しました。

echo [2/4] 仮想環境を確認中...
if not exist venv_new\Scripts\activate.bat (
    echo [ERROR] 仮想環境が見つかりません。
    echo install_web.bat を先に実行してください。
    echo.
    pause
    exit /b 1
)
echo [OK] 仮想環境が見つかりました。

echo [3/4] 仮想環境をアクティベート中...
call venv_new\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境のアクティベートに失敗しました。
    echo install_web.bat を再実行してください。
    pause
    exit /b 1
)
echo [OK] 仮想環境をアクティベートしました。

echo [4/4] Webサーバーを起動中...
echo.
echo ============================================
echo サーバーが起動しました！（高速化版）
echo ============================================
echo.
echo ⚡ 高速化機能:
echo   - HTTPセッション接続プール
echo   - 非同期履歴保存
echo   - 最適化されたタイムアウト設定
echo.
echo アクセスURL:
echo   ローカル: http://localhost:8000
echo   ネットワーク: http://0.0.0.0:8000
echo.
echo ブラウザで上記URLにアクセスしてください。
echo 終了するには Ctrl+C を押してください。
echo.
echo ============================================
echo.

python web_app.py

echo.
if %errorlevel% neq 0 (
    echo ============================================
    echo [ERROR] アプリケーションでエラーが発生しました
    echo ============================================
    echo.
    echo 考えられる原因:
    echo   1. Flaskがインストールされていない
    echo   2. web_app.pyファイルに問題がある
    echo   3. ポート8000が既に使用されている
    echo.
    echo 解決方法:
    echo   1. install_web.bat を再実行してください
    echo   2. 他のアプリケーションがポート8000を使用していないか確認
    echo   3. エラーメッセージを確認してください
    echo.
    pause
) else (
    echo.
    echo ============================================
    echo サーバーが正常に終了しました
    echo ============================================
    pause
) 
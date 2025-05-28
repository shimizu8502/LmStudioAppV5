@echo off
chcp 65001
cls
echo ============================================
echo LM Studio API Client (GUI Desktop Edition)
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

echo [4/4] GUI アプリケーションを起動中...
echo.
echo ============================================
echo GUI デスクトップアプリを起動します！
echo ============================================
echo.
echo 📱 バージョン: 20250527.1244
echo 🤖 GUI デスクトップアプリケーション
echo ⚡ 高速化機能:
echo   - HTTPセッション接続プール
echo   - 非同期履歴保存
echo   - 最適化されたタイムアウト設定
echo.
echo 💻 デスクトップアプリケーションが開きます
echo 終了するには アプリのウィンドウを閉じてください
echo.
echo ============================================
echo.

python gui_app.py

echo.
if %errorlevel% neq 0 (
    echo ============================================
    echo [ERROR] GUI アプリケーションでエラーが発生しました
    echo ============================================
    echo.
    echo 考えられる原因:
    echo   1. 必要なライブラリがインストールされていない
    echo   2. gui_app.py ファイルに問題がある
    echo   3. pyperclip ライブラリが不足している
    echo.
    echo 解決方法:
    echo   1. install_web.bat を再実行してください
    echo   2. pip install pyperclip を実行してください
    echo   3. エラーメッセージを確認してください
    echo.
    pause
) else (
    echo.
    echo ============================================
    echo GUI アプリケーションが正常に終了しました
    echo ============================================
    pause
) 
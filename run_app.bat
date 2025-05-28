@echo off
chcp 65001
cls
echo ============================================
echo LM Studio API Client - Unified Launcher
echo Ver: 20250527.1244
echo ============================================
echo.
echo 🚀 利用可能なアプリケーション:
echo.
echo   [1] 🌐 Web ブラウザ版     - http://localhost:8000
echo   [2] 💻 GUI デスクトップ版  - デスクトップアプリ
echo   [3] 🔧 インストール/更新   - 環境のセットアップ
echo   [4] 📖 ヘルプ           - 使い方とトラブルシューティング
echo   [5] 🚪 終了
echo.
echo ============================================
echo.

:MENU
set /p choice="番号を選択してください (1-5): "
echo.

if "%choice%"=="1" goto WEB
if "%choice%"=="2" goto GUI
if "%choice%"=="3" goto INSTALL
if "%choice%"=="4" goto HELP
if "%choice%"=="5" goto EXIT

echo [ERROR] 無効な選択です。1-5の数字を入力してください。
echo.
goto MENU

:WEB
echo ============================================
echo 🌐 Web ブラウザ版を起動します
echo ============================================
echo.
echo ⚡ 機能:
echo   - ブラウザで操作
echo   - ネットワーク共有可能
echo   - 複数ユーザー対応
echo   - IP別履歴管理
echo.
call run_web.bat
goto END

:GUI
echo ============================================
echo 💻 GUI デスクトップ版を起動します
echo ============================================
echo.
echo ⚡ 機能:
echo   - デスクトップアプリ
echo   - ローカル専用
echo   - 高速レスポンス
echo   - ネイティブUI
echo.
call run_gui.bat
goto END

:INSTALL
echo ============================================
echo 🔧 インストール/更新を実行します
echo ============================================
echo.
call install_web.bat
echo.
echo インストールが完了しました。
echo メニューに戻ります...
echo.
pause
cls
goto MENU

:HELP
cls
echo ============================================
echo 📖 LM Studio API Client - ヘルプ
echo Ver: 20250527.1244
echo ============================================
echo.
echo 🔧 初期設定:
echo   1. LM Studio を起動してサーバー機能をONにする
echo   2. ipconfig.ini でIPアドレスを設定（初回自動作成）
echo   3. install_web.bat でライブラリをインストール
echo.
echo 🌐 Web版の特徴:
echo   - ブラウザで http://localhost:8000 にアクセス
echo   - 複数のPCから同時利用可能
echo   - IP別に履歴を分離管理
echo   - レスポンシブデザイン
echo.
echo 💻 GUI版の特徴:
echo   - デスクトップアプリとして動作
echo   - ローカル専用（localhost として管理）
echo   - ネイティブなユーザーインターフェース
echo   - 高速なレスポンス
echo.
echo ⚡ 高速化機能（共通）:
echo   - HTTPセッション接続プール
echo   - 非同期履歴保存
echo   - 最適化されたタイムアウト設定
echo   - リアルタイム性能測定
echo.
echo 📂 ファイル構成:
echo   - web_app.py        : Webアプリケーション本体
echo   - gui_app.py        : GUIアプリケーション本体
echo   - ipconfig.ini      : API サーバー設定
echo   - prompt_history.db : 履歴データベース
echo.
echo 🔧 トラブルシューティング:
echo   - エラーが発生した場合は install_web.bat を再実行
echo   - pyperclip エラーの場合: pip install pyperclip
echo   - LM Studio API サーバーが起動しているか確認
echo   - ipconfig.ini の設定を確認
echo.
echo ============================================
pause
cls
goto MENU

:EXIT
echo.
echo 🚪 アプリケーションを終了します
echo ありがとうございました！
echo.
pause
exit /b 0

:END
echo.
echo 🔄 メニューに戻りますか？ (Y/N)
set /p return_choice="選択してください: "
if /i "%return_choice%"=="Y" (
    cls
    goto MENU
)
echo.
echo 👋 ご利用ありがとうございました！
pause
exit /b 0 
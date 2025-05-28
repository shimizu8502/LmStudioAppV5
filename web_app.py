from flask import Flask, render_template, request, jsonify, Response, stream_template
import requests
import json
import os
import sqlite3
from datetime import datetime
import configparser
import threading
import time
from queue import Queue, Empty as queue_Empty

app = Flask(__name__)

# バージョン情報
VERSION = "20250527.1244"

# LM Studio APIサーバーの設定を読み込む
def load_api_config():
    """設定ファイルからAPIサーバーの設定を読み込む"""
    config = configparser.ConfigParser()
    config_file = 'ipconfig.ini'
    
    # デフォルト設定
    default_ip = "192.168.1.166"
    default_port = "1234"
    
    if os.path.exists(config_file):
        try:
            config.read(config_file, encoding='utf-8')
            ip = config.get('API_SERVER', 'ip', fallback=default_ip)
            port = config.get('API_SERVER', 'port', fallback=default_port)
            print(f"✅ 設定ファイル読み込み成功: {config_file}")
            print(f"📡 API サーバー設定: {ip}:{port}")
        except Exception as e:
            print(f"❌ 設定ファイルの読み込みエラー: {e}")
            print("⚠️ デフォルト設定を使用します")
            ip = default_ip
            port = default_port
    else:
        # 設定ファイルが存在しない場合は作成
        print(f"⚠️ 設定ファイル '{config_file}' が見つかりません")
        print("📝 新しい設定ファイルを作成します...")
        
        # 設定ファイルの内容を手動で作成（コメント付き）
        config_content = f"""[API_SERVER]
# LM Studio API サーバーのIPアドレスとポートを設定してください
# デフォルト値: {default_ip}:{default_port}
ip = {default_ip}
port = {default_port}

# 設定例:
# ip = 192.168.1.100
# ip = localhost
# port = 1234
"""
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"✅ 設定ファイル '{config_file}' を作成しました")
            print(f"📡 デフォルト設定: {default_ip}:{default_port}")
            print(f"💡 IPアドレスを変更する場合: {config_file} ファイルを編集してください")
        except Exception as e:
            print(f"❌ 設定ファイルの作成エラー: {e}")
        
        ip = default_ip
        port = default_port
    
    return f"http://{ip}:{port}/v1"

# API URLを設定
API_URL = load_api_config()

# HTTPセッションを作成（接続プールを使用）
session = requests.Session()
session.timeout = (5, 120)  # 接続タイムアウト5秒、読み取りタイムアウト120秒

# 非同期履歴保存用のキュー
history_queue = Queue()
history_thread_running = True

# 非同期履歴保存ワーカー
def history_worker():
    """バックグラウンドで履歴を保存する"""
    while history_thread_running:
        try:
            # キューから履歴データを取得（タイムアウト1秒）
            history_data = history_queue.get(timeout=1)
            
            if history_data is None:  # 終了シグナル
                break
                
            prompt, response, api_type, client_ip = history_data
            
            # データベースに保存
            conn = sqlite3.connect('prompt_history.db')
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute(
                'INSERT INTO prompt_history (prompt, response, api_type, timestamp, client_ip) VALUES (?, ?, ?, ?, ?)',
                (prompt, response, api_type, timestamp, client_ip)
            )
            conn.commit()
            conn.close()
            
            history_queue.task_done()
            print(f"📝 履歴保存完了: {client_ip} - {api_type}")
            
        except queue_Empty:
            # タイムアウトは正常な動作なので何もしない
            continue
        except Exception as e:
            error_msg = str(e).strip()
            if error_msg:
                print(f"❌ 履歴保存エラー: {error_msg}")
            # 空のエラーメッセージの場合はスキップ

# クライアントIPアドレスを取得する関数
def get_client_ip():
    """クライアントのIPアドレスを取得する"""
    # プロキシ経由の場合は X-Forwarded-For ヘッダーを確認
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        # 複数のプロキシを経由している場合、最初のIPアドレスを取得
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()

# データベース初期化
def init_db():
    """データベースを初期化し、必要なテーブルを作成する"""
    conn = sqlite3.connect('prompt_history.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompt_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT NOT NULL,
        response TEXT,
        api_type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        client_ip TEXT
    )
    ''')
    
    # 既存のテーブルに response列がない場合は追加
    cursor.execute("PRAGMA table_info(prompt_history)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'response' not in columns:
        cursor.execute('ALTER TABLE prompt_history ADD COLUMN response TEXT')
    
    # 既存のテーブルに client_ip列がない場合は追加
    if 'client_ip' not in columns:
        cursor.execute('ALTER TABLE prompt_history ADD COLUMN client_ip TEXT')
    
    conn.commit()
    conn.close()

# アプリケーション起動時にデータベースを初期化
init_db()

# 履歴保存用のワーカースレッドを開始（デバッグモード時の重複起動を防ぐ）
if not hasattr(app, '_history_thread_started'):
    history_thread = threading.Thread(target=history_worker, daemon=True)
    history_thread.start()
    app._history_thread_started = True
    print("🚀 非同期履歴保存スレッドを開始しました")
else:
    print("⚠️ 履歴保存スレッドは既に起動済みです（デバッグモード）")

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html', version=VERSION)

@app.route('/api/client-info', methods=['GET'])
def get_client_info():
    """クライアント情報を取得する"""
    try:
        client_ip = get_client_ip()
        return jsonify({
            "client_ip": client_ip,
            "user_agent": request.headers.get('User-Agent', ''),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """利用可能なモデルの一覧を取得"""
    try:
        # セッションを使用して高速化
        response = session.get(f"{API_URL}/models", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"エラー: {response.status_code}", "details": response.text}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_completion():
    """チャット完了APIにプロンプトを送信"""
    try:
        data = request.json
        
        prompt = data.get('prompt', '')
        model = data.get('model', 'default')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 4000)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # モデルがデフォルト以外の場合は追加
        if model != "default":
            payload["model"] = model
        
        # セッションを使用して高速化
        response = session.post(
            f"{API_URL}/chat/completions", 
            headers=headers,
            json=payload,  # json=を使用してjson.dumps()を省略
            timeout=(5, 120)  # 接続5秒、読み取り120秒
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # レスポンスからメッセージ内容を抽出
            response_text = ""
            if 'choices' in result and len(result['choices']) > 0:
                response_text = result['choices'][0].get('message', {}).get('content', '')
            
            # プロンプト履歴を非同期でデータベースに保存（チャットAPI）
            client_ip = get_client_ip()
            save_prompt_history_async(prompt, response_text, 'chat', client_ip)
            
            return jsonify(result)
        else:
            return jsonify({"error": f"エラー: {response.status_code}", "details": response.text}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/text', methods=['POST'])
def text_completion():
    """テキスト完了APIにプロンプトを送信"""
    try:
        data = request.json
        
        prompt = data.get('prompt', '')
        model = data.get('model', 'default')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # モデルがデフォルト以外の場合は追加
        if model != "default":
            payload["model"] = model
        
        # セッションを使用して高速化
        response = session.post(
            f"{API_URL}/completions", 
            headers=headers,
            json=payload,  # json=を使用してjson.dumps()を省略
            timeout=(5, 120)  # 接続5秒、読み取り120秒
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # レスポンスからテキスト内容を抽出
            response_text = ""
            if 'choices' in result and len(result['choices']) > 0:
                response_text = result['choices'][0].get('text', '')
            
            # プロンプト履歴を非同期でデータベースに保存（テキストAPI）
            client_ip = get_client_ip()
            save_prompt_history_async(prompt, response_text, 'text', client_ip)
            
            return jsonify(result)
        else:
            return jsonify({"error": f"エラー: {response.status_code}", "details": response.text}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 非同期で履歴を保存する関数
def save_prompt_history_async(prompt, response, api_type, client_ip):
    """プロンプト履歴を非同期で保存する"""
    try:
        history_queue.put((prompt, response, api_type, client_ip), timeout=1)
        print(f"📝 履歴保存キューに追加: {client_ip} - {api_type}")
    except Exception as e:
        print(f"❌ 履歴キューエラー: {e}")

# プロンプト履歴をデータベースに保存する関数（同期版、互換性のため残す）
def save_prompt_history(prompt, response, api_type, client_ip):
    """プロンプト履歴をデータベースに保存する（同期版）"""
    try:
        conn = sqlite3.connect('prompt_history.db')
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute(
            'INSERT INTO prompt_history (prompt, response, api_type, timestamp, client_ip) VALUES (?, ?, ?, ?, ?)',
            (prompt, response, api_type, timestamp, client_ip)
        )
        conn.commit()
        conn.close()
        print(f"📝 履歴保存: {client_ip} - {api_type}")
    except Exception as e:
        print(f"❌ 履歴の保存中にエラーが発生しました: {e}")

# プロンプト履歴のAPI
@app.route('/api/prompt-history', methods=['GET'])
def get_prompt_history():
    """現在のクライアントIPのプロンプト履歴を取得する"""
    try:
        client_ip = get_client_ip()
        conn = sqlite3.connect('prompt_history.db')
        conn.row_factory = sqlite3.Row  # 辞書形式で結果を取得
        cursor = conn.cursor()
        
        # 現在のクライアントIPの最新20件を取得
        cursor.execute(
            'SELECT * FROM prompt_history WHERE client_ip = ? OR client_ip IS NULL ORDER BY id DESC LIMIT 20', 
            (client_ip,)
        )
        history = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        print(f"📖 履歴取得: {client_ip} - {len(history)}件")
        return jsonify({"history": history, "client_ip": client_ip})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/prompt-history', methods=['DELETE'])
def clear_prompt_history():
    """現在のクライアントIPのプロンプト履歴をすべて削除する"""
    try:
        client_ip = get_client_ip()
        conn = sqlite3.connect('prompt_history.db')
        cursor = conn.cursor()
        
        # 現在のクライアントIPの履歴のみ削除
        cursor.execute('DELETE FROM prompt_history WHERE client_ip = ? OR client_ip IS NULL', (client_ip,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        print(f"🗑️ 履歴削除: {client_ip} - {deleted_count}件")
        return jsonify({"message": f"履歴を削除しました ({deleted_count}件)", "client_ip": client_ip})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/prompt-history/<int:prompt_id>', methods=['DELETE'])
def delete_prompt_history(prompt_id):
    """指定されたIDのプロンプト履歴を削除する（現在のクライアントIPのもののみ）"""
    try:
        client_ip = get_client_ip()
        conn = sqlite3.connect('prompt_history.db')
        cursor = conn.cursor()
        
        # 現在のクライアントIPのもののみ削除
        cursor.execute(
            'DELETE FROM prompt_history WHERE id = ? AND (client_ip = ? OR client_ip IS NULL)', 
            (prompt_id, client_ip)
        )
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            print(f"🗑️ 個別削除: {client_ip} - ID:{prompt_id}")
            return jsonify({"message": f"ID: {prompt_id}の履歴を削除しました", "client_ip": client_ip})
        else:
            return jsonify({"error": "指定された履歴が見つからないか、削除権限がありません"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# テンプレートディレクトリがなければ作成
if not os.path.exists('templates'):
    os.makedirs('templates')

# アプリケーション終了時の処理
def shutdown_handler():
    """アプリケーション終了時に呼び出される"""
    global history_thread_running
    print("\n🛑 アプリケーションを終了中...")
    
    # 履歴保存スレッドを停止
    history_thread_running = False
    history_queue.put(None)  # 終了シグナル
    
    # セッションを閉じる
    session.close()
    
    print("✅ 終了処理が完了しました")

if __name__ == '__main__':
    try:
        print("=" * 60)
        print("🚀 LM Studio Web アプリケーション起動中...")
        print(f"📱 バージョン: {VERSION}")
        print(f"📡 API サーバー: {API_URL}")
        print("🌐 Web サーバー: http://localhost:8000")
        print("💡 設定変更: ipconfig.ini ファイルを編集してください")
        print("⚡ 高速化機能:")
        print("  - HTTPセッション接続プール")
        print("  - 非同期履歴保存")
        print("  - 最適化されたタイムアウト設定")
        print("=" * 60)
        
        # 環境変数でデバッグモードを制御（デフォルトはプロダクションモード）
        debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        if debug_mode:
            print("⚠️ デバッグモードで起動します（開発用）")
        else:
            print("🔒 プロダクションモードで起動します（推奨）")
        
        app.run(debug=debug_mode, host='0.0.0.0', port=8000, use_reloader=False)
    except KeyboardInterrupt:
        shutdown_handler()
    except Exception as e:
        print(f"❌ アプリケーションエラー: {e}")
        shutdown_handler() 
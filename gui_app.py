#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Studio API GUI クライアント - デスクトップ版
Web版と同じ機能をデスクトップアプリで提供

Version: 20250527.1244
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import requests
import json
import sqlite3
import threading
import time
from datetime import datetime
import configparser
import os
import sys
from queue import Queue, Empty as queue_Empty
import pyperclip  # クリップボード操作用

class LMStudioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LM Studio API Client - Desktop Edition")
        self.root.geometry("1200x800")
        
        # バージョン情報
        self.version = "20250527.1244"
        
        # APIサーバー設定
        self.api_url = self.load_api_config()
        
        # HTTPセッション
        self.session = requests.Session()
        self.session.timeout = (5, 120)
        
        # 非同期履歴保存用
        self.history_queue = Queue()
        self.history_thread_running = True
        
        # データベース初期化
        self.init_db()
        
        # GUI構築
        self.create_widgets()
        
        # 履歴保存スレッド開始
        self.start_history_worker()
        
        # 初期データ読み込み
        self.load_models()
        self.load_history()
        
        # 終了時の処理を設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_api_config(self):
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
            ip = default_ip
            port = default_port
        
        return f"http://{ip}:{port}/v1"
    
    def init_db(self):
        """データベースを初期化"""
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
        
        # 既存のテーブルに columns がない場合は追加
        cursor.execute("PRAGMA table_info(prompt_history)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'response' not in columns:
            cursor.execute('ALTER TABLE prompt_history ADD COLUMN response TEXT')
        if 'client_ip' not in columns:
            cursor.execute('ALTER TABLE prompt_history ADD COLUMN client_ip TEXT')
        
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        """GUI要素を作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 上部のタイトルとバージョン情報
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="🤖 LM Studio API Client - Desktop Edition", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_frame, text=f"📱 Ver: {self.version}", 
                 font=("Arial", 10)).pack(side=tk.RIGHT)
        
        # 左右のペイン
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左側：履歴パネル
        self.create_history_panel(paned_window)
        
        # 右側：メインパネル
        self.create_main_panel(paned_window)
        
        # ステータスバー
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text=f"📡 API Server: {self.api_url}")
        self.status_label.pack(side=tk.LEFT)
        
        self.client_label = ttk.Label(status_frame, text="💻 Client: localhost")
        self.client_label.pack(side=tk.RIGHT)
    
    def create_history_panel(self, parent):
        """履歴パネルを作成"""
        history_frame = ttk.LabelFrame(parent, text="📚 プロンプト履歴", padding="10")
        parent.add(history_frame, weight=1)
        
        # 履歴操作ボタン
        button_frame = ttk.Frame(history_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="🔄 更新", 
                  command=self.load_history).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🗑️ 全削除", 
                  command=self.clear_all_history).pack(side=tk.LEFT)
        
        # 履歴リスト
        self.history_tree = ttk.Treeview(history_frame, columns=("timestamp", "api", "prompt"), 
                                        show="tree headings", height=15)
        
        # 列の設定
        self.history_tree.heading("#0", text="ID")
        self.history_tree.heading("timestamp", text="時刻")
        self.history_tree.heading("api", text="API")
        self.history_tree.heading("prompt", text="プロンプト")
        
        self.history_tree.column("#0", width=50)
        self.history_tree.column("timestamp", width=120)
        self.history_tree.column("api", width=60)
        self.history_tree.column("prompt", width=200)
        
        # スクロールバー
        history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                     command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 履歴のコンテキストメニュー
        self.history_context_menu = tk.Menu(self.root, tearoff=0)
        self.history_context_menu.add_command(label="✅ 使用", command=self.use_history_item)
        self.history_context_menu.add_command(label="✏️ 編集", command=self.edit_history_item)
        self.history_context_menu.add_command(label="📋 プロンプトコピー", command=self.copy_history_prompt)
        self.history_context_menu.add_command(label="📋 回答コピー", command=self.copy_history_response)
        self.history_context_menu.add_separator()
        self.history_context_menu.add_command(label="🗑️ 削除", command=self.delete_history_item)
        
        self.history_tree.bind("<Button-3>", self.show_history_context_menu)
        self.history_tree.bind("<Double-1>", self.use_history_item)
    
    def create_main_panel(self, parent):
        """メインパネルを作成"""
        main_frame = ttk.Frame(parent)
        parent.add(main_frame, weight=2)
        
        # 設定パネル
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ 設定", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第1行：モデルとAPI選択
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row1, text="🤖 モデル:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(row1, textvariable=self.model_var, width=30)
        self.model_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1, text="🔧 API:").pack(side=tk.LEFT)
        self.api_type_var = tk.StringVar(value="chat")
        ttk.Radiobutton(row1, text="Chat", variable=self.api_type_var, 
                       value="chat").pack(side=tk.LEFT, padx=(5, 10))
        ttk.Radiobutton(row1, text="Text", variable=self.api_type_var, 
                       value="text").pack(side=tk.LEFT)
        
        # 第2行：パラメータ
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X)
        
        ttk.Label(row2, text="🌡️ Temperature:").pack(side=tk.LEFT)
        self.temperature_var = tk.DoubleVar(value=0.7)
        temp_scale = ttk.Scale(row2, from_=0.0, to=1.0, orient=tk.HORIZONTAL, 
                              variable=self.temperature_var, length=150)
        temp_scale.pack(side=tk.LEFT, padx=(5, 10))
        self.temp_label = ttk.Label(row2, text="0.7")
        self.temp_label.pack(side=tk.LEFT, padx=(0, 20))
        self.temperature_var.trace('w', self.update_temp_label)
        
        ttk.Label(row2, text="📏 Max Tokens:").pack(side=tk.LEFT)
        self.max_tokens_var = tk.IntVar(value=4000)
        tokens_spin = ttk.Spinbox(row2, from_=100, to=4000, textvariable=self.max_tokens_var, 
                                 width=10)
        tokens_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        # プロンプト入力エリア
        prompt_frame = ttk.LabelFrame(main_frame, text="✍️ プロンプト入力", padding="10")
        prompt_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=8, wrap=tk.WORD)
        self.prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 送信ボタンとクリアボタン
        button_frame = ttk.Frame(prompt_frame)
        button_frame.pack(fill=tk.X)
        
        self.send_button = ttk.Button(button_frame, text="🚀 送信", command=self.send_request)
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="🗑️ クリア", 
                  command=lambda: self.prompt_text.delete(1.0, tk.END)).pack(side=tk.LEFT)
        
        # 文字数表示
        self.char_count_label = ttk.Label(button_frame, text="文字数: 0")
        self.char_count_label.pack(side=tk.RIGHT)
        self.prompt_text.bind('<KeyRelease>', self.update_char_count)
        
        # レスポンス表示エリア
        response_frame = ttk.LabelFrame(main_frame, text="💬 レスポンス", padding="10")
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        self.response_text = scrolledtext.ScrolledText(response_frame, height=8, wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # レスポンスボタン
        response_button_frame = ttk.Frame(response_frame)
        response_button_frame.pack(fill=tk.X)
        
        ttk.Button(response_button_frame, text="📋 コピー", 
                  command=self.copy_response).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(response_button_frame, text="🗑️ クリア", 
                  command=lambda: self.response_text.delete(1.0, tk.END)).pack(side=tk.LEFT)
        
        # レスポンス時間表示
        self.response_time_label = ttk.Label(response_button_frame, text="")
        self.response_time_label.pack(side=tk.RIGHT)
    
    def update_temp_label(self, *args):
        """Temperature ラベルを更新"""
        self.temp_label.config(text=f"{self.temperature_var.get():.1f}")
    
    def update_char_count(self, event=None):
        """文字数カウントを更新"""
        content = self.prompt_text.get(1.0, tk.END).strip()
        count = len(content)
        self.char_count_label.config(text=f"文字数: {count}")
    
    def load_models(self):
        """利用可能なモデルを読み込み"""
        def fetch_models():
            try:
                response = self.session.get(f"{self.api_url}/models", timeout=10)
                if response.status_code == 200:
                    models_data = response.json()
                    model_names = [model['id'] for model in models_data.get('data', [])]
                    
                    # UIを更新（メインスレッドで実行）
                    self.root.after(0, lambda: self.update_models_ui(model_names))
                else:
                    self.root.after(0, lambda: self.show_error(f"モデル取得エラー: {response.status_code}"))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"モデル取得エラー: {str(e)}"))
        
        threading.Thread(target=fetch_models, daemon=True).start()
    
    def update_models_ui(self, model_names):
        """モデル一覧UIを更新"""
        self.model_combo['values'] = model_names
        if model_names:
            self.model_combo.set(model_names[0])
        self.status_label.config(text=f"📡 API Server: {self.api_url} ({len(model_names)} models)")
    
    def send_request(self):
        """APIリクエストを送信"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showwarning("警告", "プロンプトを入力してください")
            return
        
        # ボタンを無効化
        self.send_button.config(state=tk.DISABLED, text="📡 送信中...")
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, "🤔 AIが考え中...")
        
        def send_async():
            start_time = time.time()
            try:
                # リクエストデータを準備
                model = self.model_var.get() if self.model_var.get() else "default"
                temperature = self.temperature_var.get()
                max_tokens = self.max_tokens_var.get()
                api_type = self.api_type_var.get()
                
                if api_type == "chat":
                    payload = {
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    if model != "default":
                        payload["model"] = model
                    
                    response = self.session.post(
                        f"{self.api_url}/chat/completions",
                        json=payload,
                        timeout=(5, 120)
                    )
                else:  # text completion
                    payload = {
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    if model != "default":
                        payload["model"] = model
                    
                    response = self.session.post(
                        f"{self.api_url}/completions",
                        json=payload,
                        timeout=(5, 120)
                    )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ミリ秒
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # レスポンステキストを抽出
                    if api_type == "chat":
                        response_text = ""
                        if 'choices' in result and len(result['choices']) > 0:
                            response_text = result['choices'][0].get('message', {}).get('content', '')
                    else:
                        response_text = ""
                        if 'choices' in result and len(result['choices']) > 0:
                            response_text = result['choices'][0].get('text', '')
                    
                    # 履歴を保存
                    self.save_prompt_history_async(prompt, response_text, api_type, "localhost")
                    
                    # UIを更新
                    self.root.after(0, lambda: self.update_response_ui(response_text, response_time, True))
                    
                else:
                    error_msg = f"エラー {response.status_code}: {response.text}"
                    self.root.after(0, lambda: self.update_response_ui(error_msg, response_time, False))
                    
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                error_msg = f"リクエストエラー: {str(e)}"
                self.root.after(0, lambda: self.update_response_ui(error_msg, response_time, False))
        
        threading.Thread(target=send_async, daemon=True).start()
    
    def update_response_ui(self, response_text, response_time, is_success):
        """レスポンスUIを更新"""
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, response_text)
        
        # ボタンを再有効化
        self.send_button.config(state=tk.NORMAL, text="🚀 送信")
        
        # レスポンス時間を表示
        if is_success:
            self.response_time_label.config(text=f"⚡ {response_time:.0f}ms")
        else:
            self.response_time_label.config(text=f"❌ {response_time:.0f}ms")
        
        # 履歴は履歴保存ワーカーで更新されるので、ここでは削除
    
    def copy_response(self):
        """レスポンスをクリップボードにコピー"""
        response_content = self.response_text.get(1.0, tk.END).strip()
        if response_content:
            try:
                pyperclip.copy(response_content)
                messagebox.showinfo("コピー完了", "レスポンスをクリップボードにコピーしました")
            except Exception as e:
                messagebox.showerror("コピーエラー", f"コピーに失敗しました: {str(e)}")
        else:
            messagebox.showwarning("警告", "コピーするレスポンスがありません")
    
    def start_history_worker(self):
        """履歴保存ワーカーを開始"""
        def history_worker():
            while self.history_thread_running:
                try:
                    history_data = self.history_queue.get(timeout=1)
                    if history_data is None:
                        break
                    
                    prompt, response, api_type, client_ip = history_data
                    
                    conn = sqlite3.connect('prompt_history.db')
                    cursor = conn.cursor()
                    timestamp = datetime.now().isoformat()
                    cursor.execute(
                        'INSERT INTO prompt_history (prompt, response, api_type, timestamp, client_ip) VALUES (?, ?, ?, ?, ?)',
                        (prompt, response, api_type, timestamp, client_ip)
                    )
                    conn.commit()
                    conn.close()
                    
                    # 履歴保存完了後にUIを更新
                    self.root.after(0, self.load_history)
                    
                    self.history_queue.task_done()
                    
                except queue_Empty:
                    continue
                except Exception as e:
                    print(f"❌ 履歴保存エラー: {e}")
        
        threading.Thread(target=history_worker, daemon=True).start()
    
    def save_prompt_history_async(self, prompt, response, api_type, client_ip):
        """履歴を非同期で保存"""
        try:
            self.history_queue.put((prompt, response, api_type, client_ip), timeout=1)
        except Exception as e:
            print(f"❌ 履歴キューエラー: {e}")
    
    def load_history(self):
        """履歴を読み込み"""
        try:
            conn = sqlite3.connect('prompt_history.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM prompt_history WHERE client_ip = ? OR client_ip IS NULL ORDER BY id DESC LIMIT 50',
                ("localhost",)
            )
            history = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # 履歴ツリーをクリア
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # 履歴項目を追加
            for item in history:
                # タイムスタンプをフォーマット
                timestamp = datetime.fromisoformat(item['timestamp'])
                time_str = timestamp.strftime("%m/%d %H:%M")
                
                # プロンプトを短縮
                prompt_preview = item['prompt'][:50] + "..." if len(item['prompt']) > 50 else item['prompt']
                
                self.history_tree.insert("", "end", iid=item['id'],
                                       text=str(item['id']),
                                       values=(time_str, item['api_type'], prompt_preview))
            
        except Exception as e:
            self.show_error(f"履歴読み込みエラー: {str(e)}")
    
    def show_history_context_menu(self, event):
        """履歴のコンテキストメニューを表示"""
        item = self.history_tree.selection()[0] if self.history_tree.selection() else None
        if item:
            self.history_context_menu.post(event.x_root, event.y_root)
    
    def use_history_item(self, event=None):
        """履歴項目を使用"""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        history_data = self.get_history_item_data(item_id)
        if history_data:
            # プロンプトを設定
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, history_data['prompt'])
            
            # レスポンスを設定
            if history_data['response']:
                self.response_text.delete(1.0, tk.END)
                self.response_text.insert(1.0, history_data['response'])
            
            # API タイプを設定
            self.api_type_var.set(history_data['api_type'])
    
    def edit_history_item(self):
        """履歴項目を編集"""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        history_data = self.get_history_item_data(item_id)
        if history_data:
            # プロンプトのみを設定（編集用）
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, history_data['prompt'])
            
            # API タイプを設定
            self.api_type_var.set(history_data['api_type'])
    
    def copy_history_prompt(self):
        """履歴のプロンプトをコピー"""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        history_data = self.get_history_item_data(item_id)
        if history_data and history_data['prompt']:
            try:
                pyperclip.copy(history_data['prompt'])
                messagebox.showinfo("コピー完了", "プロンプトをクリップボードにコピーしました")
            except Exception as e:
                messagebox.showerror("コピーエラー", f"コピーに失敗しました: {str(e)}")
    
    def copy_history_response(self):
        """履歴の回答をコピー"""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        history_data = self.get_history_item_data(item_id)
        if history_data and history_data['response']:
            try:
                pyperclip.copy(history_data['response'])
                messagebox.showinfo("コピー完了", "回答をクリップボードにコピーしました")
            except Exception as e:
                messagebox.showerror("コピーエラー", f"コピーに失敗しました: {str(e)}")
        else:
            messagebox.showwarning("警告", "コピーする回答がありません")
    
    def delete_history_item(self):
        """履歴項目を削除"""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        
        if messagebox.askyesno("確認", "この履歴項目を削除しますか？"):
            try:
                conn = sqlite3.connect('prompt_history.db')
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM prompt_history WHERE id = ? AND (client_ip = ? OR client_ip IS NULL)',
                    (item_id, "localhost")
                )
                conn.commit()
                conn.close()
                
                self.load_history()
                messagebox.showinfo("削除完了", "履歴項目を削除しました")
            except Exception as e:
                messagebox.showerror("削除エラー", f"削除に失敗しました: {str(e)}")
    
    def clear_all_history(self):
        """全ての履歴を削除"""
        if messagebox.askyesno("確認", "すべての履歴を削除しますか？この操作は取り消せません。"):
            try:
                conn = sqlite3.connect('prompt_history.db')
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM prompt_history WHERE client_ip = ? OR client_ip IS NULL',
                    ("localhost",)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                self.load_history()
                messagebox.showinfo("削除完了", f"{deleted_count}件の履歴を削除しました")
            except Exception as e:
                messagebox.showerror("削除エラー", f"削除に失敗しました: {str(e)}")
    
    def get_history_item_data(self, item_id):
        """履歴項目のデータを取得"""
        try:
            conn = sqlite3.connect('prompt_history.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM prompt_history WHERE id = ? AND (client_ip = ? OR client_ip IS NULL)',
                (item_id, "localhost")
            )
            result = cursor.fetchone()
            conn.close()
            return dict(result) if result else None
        except Exception as e:
            self.show_error(f"履歴取得エラー: {str(e)}")
            return None
    
    def show_error(self, message):
        """エラーメッセージを表示"""
        messagebox.showerror("エラー", message)
        print(f"❌ {message}")
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        print("🛑 アプリケーションを終了中...")
        
        # 履歴保存スレッドを停止
        self.history_thread_running = False
        self.history_queue.put(None)
        
        # セッションを閉じる
        self.session.close()
        
        print("✅ 終了処理が完了しました")
        self.root.destroy()

def main():
    """メイン関数"""
    try:
        print("=" * 60)
        print("🚀 LM Studio GUI アプリケーション起動中...")
        print("Ver: 20250527.1244")
        print("=" * 60)
        
        root = tk.Tk()
        app = LMStudioGUI(root)
        root.mainloop()
        
    except ImportError as e:
        if "pyperclip" in str(e):
            print("❌ pyperclip ライブラリが必要です")
            print("インストール: pip install pyperclip")
        else:
            print(f"❌ インポートエラー: {e}")
    except Exception as e:
        print(f"❌ アプリケーションエラー: {e}")

if __name__ == "__main__":
    main() 
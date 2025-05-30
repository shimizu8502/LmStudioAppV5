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

# ツールチップクラス
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.tooltip_window = None

    def on_enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, background="#ffffe0", 
                        relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()

    def on_leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class LMStudioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 LM Studio API Client - Desktop Edition")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # アプリケーションアイコンを設定（オプション）
        try:
            # アイコンファイルが存在する場合のみ設定
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass
        
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
        
        # テーマとスタイルを設定
        self.setup_theme_and_styles()
        
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
    
    def setup_theme_and_styles(self):
        """テーマとカスタムスタイルを設定"""
        # モダンなテーマを適用
        style = ttk.Style()
        
        # 利用可能なテーマから最適なものを選択
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # カスタムカラーパレット
        colors = {
            'primary': '#2c3e50',      # ダークブルー
            'secondary': '#3498db',    # ブルー
            'accent': '#e74c3c',       # レッド
            'success': '#27ae60',      # グリーン
            'warning': '#f39c12',      # オレンジ
            'light': '#ecf0f1',        # ライトグレー
            'dark': '#34495e',         # ダークグレー
            'white': '#ffffff',
            'bg_main': '#f8f9fa',      # メイン背景
            'bg_panel': '#ffffff',     # パネル背景
        }
        
        # ルートウィンドウの背景色
        self.root.configure(bg=colors['bg_main'])
        
        # カスタムボタンスタイル
        style.configure('Primary.TButton',
                       background=colors['secondary'],
                       foreground='black',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(10, 5))
        style.map('Primary.TButton',
                 background=[('active', colors['primary'])])
        
        style.configure('Success.TButton',
                       background=colors['success'],
                       foreground='black',
                       font=('Segoe UI', 9),
                       padding=(8, 4))
        style.map('Success.TButton',
                 background=[('active', '#229954')])
        
        style.configure('Warning.TButton',
                       background=colors['warning'],
                       foreground='black',
                       font=('Segoe UI', 9),
                       padding=(8, 4))
        style.map('Warning.TButton',
                 background=[('active', '#e67e22')])
        
        style.configure('Danger.TButton',
                       background=colors['accent'],
                       foreground='black',
                       font=('Segoe UI', 9),
                       padding=(8, 4))
        style.map('Danger.TButton',
                 background=[('active', '#c0392b')])
        
        # カスタムラベルフレームスタイル
        style.configure('Card.TLabelframe',
                       background=colors['bg_panel'],
                       borderwidth=2,
                       relief='raised')
        style.configure('Card.TLabelframe.Label',
                       background=colors['bg_panel'],
                       foreground=colors['primary'],
                       font=('Segoe UI', 11, 'bold'))
        
        # プログレスバースタイル
        style.configure('Custom.Horizontal.TProgressbar',
                       background=colors['secondary'],
                       troughcolor=colors['light'],
                       borderwidth=0,
                       lightcolor=colors['secondary'],
                       darkcolor=colors['secondary'])
        
        # フレームスタイル
        style.configure('Main.TFrame',
                       background=colors['bg_main'])
        style.configure('Panel.TFrame',
                       background=colors['bg_panel'])
        
        # ラベルスタイル
        style.configure('Title.TLabel',
                       background=colors['bg_main'],
                       foreground=colors['primary'],
                       font=('Segoe UI', 18, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=colors['bg_main'],
                       foreground=colors['dark'],
                       font=('Segoe UI', 10))
        style.configure('Status.TLabel',
                       background=colors['bg_main'],
                       foreground=colors['dark'],
                       font=('Segoe UI', 9))
        
        # コンボボックススタイル
        style.configure('Custom.TCombobox',
                       fieldbackground=colors['white'],
                       background=colors['light'],
                       font=('Segoe UI', 10))
        
        # ツリービュースタイル
        style.configure('Custom.Treeview',
                       background=colors['white'],
                       foreground=colors['dark'],
                       fieldbackground=colors['white'],
                       font=('Segoe UI', 9))
        style.configure('Custom.Treeview.Heading',
                       background=colors['light'],
                       foreground=colors['primary'],
                       font=('Segoe UI', 9, 'bold'))
        
        self.colors = colors

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
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 上部のタイトルとバージョン情報
        title_frame = ttk.Frame(main_frame, style='Main.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🤖 LM Studio API Client", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        version_frame = ttk.Frame(title_frame, style='Main.TFrame')
        version_frame.pack(side=tk.RIGHT)
        
        ttk.Label(version_frame, text="Desktop Edition", 
                 style='Subtitle.TLabel').pack()
        ttk.Label(version_frame, text=f"Version: {self.version}", 
                 style='Status.TLabel').pack()
        
        # プログレスバー（初期は非表示）
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', 
                                       style='Custom.Horizontal.TProgressbar')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        self.progress.pack_forget()  # 初期は非表示
        
        # 左右のペイン
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左側：履歴パネル
        self.create_history_panel(paned_window)
        
        # 右側：メインパネル
        self.create_main_panel(paned_window)
        
        # ステータスバー
        status_frame = ttk.Frame(main_frame, style='Main.TFrame')
        status_frame.pack(fill=tk.X, pady=(15, 0))
        
        # ステータス情報をより見やすく
        status_left = ttk.Frame(status_frame, style='Main.TFrame')
        status_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(status_left, text=f"📡 API Server: {self.api_url}", 
                                     style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        status_right = ttk.Frame(status_frame, style='Main.TFrame')
        status_right.pack(side=tk.RIGHT)
        
        self.client_label = ttk.Label(status_right, text="💻 Client: localhost", 
                                     style='Status.TLabel')
        self.client_label.pack(side=tk.RIGHT)
    
    def create_history_panel(self, parent):
        """履歴パネルを作成"""
        history_frame = ttk.LabelFrame(parent, text="📚 プロンプト履歴", 
                                      style='Card.TLabelframe', padding="15")
        parent.add(history_frame, weight=1)
        
        # 履歴操作ボタン
        button_frame = ttk.Frame(history_frame, style='Panel.TFrame')
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        refresh_btn = ttk.Button(button_frame, text="🔄 更新", 
                                command=self.load_history, style='Success.TButton')
        refresh_btn.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(refresh_btn, "履歴を最新の状態に更新します")
        
        clear_btn = ttk.Button(button_frame, text="🗑️ 全削除", 
                              command=self.clear_all_history, style='Danger.TButton')
        clear_btn.pack(side=tk.LEFT)
        ToolTip(clear_btn, "すべての履歴を削除します（取り消しできません）")
        
        # 履歴数表示
        self.history_count_label = ttk.Label(button_frame, text="", style='Status.TLabel')
        self.history_count_label.pack(side=tk.RIGHT)
        
        # 履歴リスト
        tree_frame = ttk.Frame(history_frame, style='Panel.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_tree = ttk.Treeview(tree_frame, columns=("timestamp", "api", "prompt"), 
                                        show="tree headings", height=18, style='Custom.Treeview')
        
        # 列の設定
        self.history_tree.heading("#0", text="ID")
        self.history_tree.heading("timestamp", text="📅 時刻")
        self.history_tree.heading("api", text="🔧 API")
        self.history_tree.heading("prompt", text="✍️ プロンプト")
        
        self.history_tree.column("#0", width=60, anchor='center')
        self.history_tree.column("timestamp", width=130, anchor='center')
        self.history_tree.column("api", width=70, anchor='center')
        self.history_tree.column("prompt", width=250)
        
        # スクロールバー
        history_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                     command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 履歴のコンテキストメニュー
        self.history_context_menu = tk.Menu(self.root, tearoff=0, 
                                           font=('Segoe UI', 9))
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
        main_frame = ttk.Frame(parent, style='Main.TFrame')
        parent.add(main_frame, weight=2)
        
        # 設定パネル
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ 設定", 
                                       style='Card.TLabelframe', padding="15")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 第1行：モデルとAPI選択
        row1 = ttk.Frame(settings_frame, style='Panel.TFrame')
        row1.pack(fill=tk.X, pady=(0, 10))
        
        # モデル選択
        model_frame = ttk.Frame(row1, style='Panel.TFrame')
        model_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        
        ttk.Label(model_frame, text="🤖 モデル:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                       style='Custom.TCombobox', font=('Segoe UI', 10))
        self.model_combo.pack(fill=tk.X, pady=(5, 0))
        ToolTip(self.model_combo, "使用するAIモデルを選択してください")
        
        # API選択
        api_frame = ttk.Frame(row1, style='Panel.TFrame')
        api_frame.pack(side=tk.RIGHT)
        
        ttk.Label(api_frame, text="🔧 API タイプ:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        api_buttons_frame = ttk.Frame(api_frame, style='Panel.TFrame')
        api_buttons_frame.pack(pady=(5, 0))
        
        self.api_type_var = tk.StringVar(value="chat")
        chat_radio = ttk.Radiobutton(api_buttons_frame, text="💬 Chat", 
                                    variable=self.api_type_var, value="chat")
        chat_radio.pack(side=tk.LEFT, padx=(0, 15))
        ToolTip(chat_radio, "対話形式のAPI（推奨）")
        
        text_radio = ttk.Radiobutton(api_buttons_frame, text="📝 Text", 
                                    variable=self.api_type_var, value="text")
        text_radio.pack(side=tk.LEFT)
        ToolTip(text_radio, "テキスト補完API")
        
        # 第2行：パラメータ
        row2 = ttk.Frame(settings_frame, style='Panel.TFrame')
        row2.pack(fill=tk.X)
        
        # Temperature設定
        temp_frame = ttk.Frame(row2, style='Panel.TFrame')
        temp_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        
        temp_label_frame = ttk.Frame(temp_frame, style='Panel.TFrame')
        temp_label_frame.pack(fill=tk.X)
        
        ttk.Label(temp_label_frame, text="🌡️ Temperature:", 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        self.temp_value_label = ttk.Label(temp_label_frame, text="0.7", 
                                         font=('Segoe UI', 10, 'bold'), 
                                         foreground=self.colors['secondary'])
        self.temp_value_label.pack(side=tk.RIGHT)
        
        self.temperature_var = tk.DoubleVar(value=0.7)
        temp_scale = ttk.Scale(temp_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, 
                              variable=self.temperature_var, length=200)
        temp_scale.pack(fill=tk.X, pady=(5, 0))
        self.temperature_var.trace('w', self.update_temp_label)
        ToolTip(temp_scale, "応答の創造性を調整（0.0=保守的、1.0=創造的）")
        
        # Max Tokens設定
        tokens_frame = ttk.Frame(row2, style='Panel.TFrame')
        tokens_frame.pack(side=tk.RIGHT)
        
        ttk.Label(tokens_frame, text="📏 Max Tokens:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.max_tokens_var = tk.IntVar(value=4000)
        tokens_spin = ttk.Spinbox(tokens_frame, from_=100, to=8000, 
                                 textvariable=self.max_tokens_var, width=12,
                                 font=('Segoe UI', 10))
        tokens_spin.pack(pady=(5, 0))
        ToolTip(tokens_spin, "生成する最大トークン数")
        
        # プロンプト入力エリア
        prompt_frame = ttk.LabelFrame(main_frame, text="✍️ プロンプト入力", 
                                     style='Card.TLabelframe', padding="15")
        prompt_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # プロンプトテキストエリア
        prompt_text_frame = ttk.Frame(prompt_frame, style='Panel.TFrame')
        prompt_text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_text_frame, height=6, wrap=tk.WORD,
                                                    font=('Consolas', 11),
                                                    bg=self.colors['white'],
                                                    fg=self.colors['dark'],
                                                    selectbackground=self.colors['secondary'],
                                                    insertbackground=self.colors['primary'])
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        
        # プロンプト操作ボタン
        prompt_buttons_frame = ttk.Frame(prompt_frame, style='Panel.TFrame')
        prompt_buttons_frame.pack(fill=tk.X)
        
        # 左側のボタン
        left_buttons = ttk.Frame(prompt_buttons_frame, style='Panel.TFrame')
        left_buttons.pack(side=tk.LEFT)
        
        self.send_button = ttk.Button(left_buttons, text="🚀 送信", 
                                     command=self.send_request, style='Primary.TButton')
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(self.send_button, "プロンプトをAIに送信します")
        
        clear_prompt_btn = ttk.Button(left_buttons, text="🗑️ クリア", 
                                     command=lambda: self.prompt_text.delete(1.0, tk.END),
                                     style='Warning.TButton')
        clear_prompt_btn.pack(side=tk.LEFT)
        ToolTip(clear_prompt_btn, "プロンプト入力欄をクリアします")
        
        # 右側の情報表示
        right_info = ttk.Frame(prompt_buttons_frame, style='Panel.TFrame')
        right_info.pack(side=tk.RIGHT)
        
        self.char_count_label = ttk.Label(right_info, text="文字数: 0", 
                                         style='Status.TLabel')
        self.char_count_label.pack(side=tk.RIGHT)
        self.prompt_text.bind('<KeyRelease>', self.update_char_count)
        self.prompt_text.bind('<ButtonRelease>', self.update_char_count)
        
        # レスポンス表示エリア
        response_frame = ttk.LabelFrame(main_frame, text="💬 AIレスポンス", 
                                       style='Card.TLabelframe', padding="15")
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        # レスポンステキストエリア
        response_text_frame = ttk.Frame(response_frame, style='Panel.TFrame')
        response_text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.response_text = scrolledtext.ScrolledText(response_text_frame, height=6, wrap=tk.WORD,
                                                      font=('Segoe UI', 11),
                                                      bg=self.colors['white'],
                                                      fg=self.colors['dark'],
                                                      selectbackground=self.colors['secondary'],
                                                      state=tk.DISABLED)
        self.response_text.pack(fill=tk.BOTH, expand=True)
        
        # レスポンス操作ボタン
        response_buttons_frame = ttk.Frame(response_frame, style='Panel.TFrame')
        response_buttons_frame.pack(fill=tk.X)
        
        # 左側のボタン
        response_left_buttons = ttk.Frame(response_buttons_frame, style='Panel.TFrame')
        response_left_buttons.pack(side=tk.LEFT)
        
        copy_btn = ttk.Button(response_left_buttons, text="📋 コピー", 
                             command=self.copy_response, style='Success.TButton')
        copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(copy_btn, "レスポンスをクリップボードにコピーします")
        
        clear_response_btn = ttk.Button(response_left_buttons, text="🗑️ クリア", 
                                       command=self.clear_response, style='Warning.TButton')
        clear_response_btn.pack(side=tk.LEFT)
        ToolTip(clear_response_btn, "レスポンス表示をクリアします")
        
        # 右側の情報表示
        response_right_info = ttk.Frame(response_buttons_frame, style='Panel.TFrame')
        response_right_info.pack(side=tk.RIGHT)
        
        self.response_time_label = ttk.Label(response_right_info, text="", 
                                           style='Status.TLabel')
        self.response_time_label.pack(side=tk.RIGHT)
    
    def clear_response(self):
        """レスポンス表示をクリア"""
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.response_time_label.config(text="")
    
    def update_temp_label(self, *args):
        """Temperature ラベルを更新"""
        value = self.temperature_var.get()
        self.temp_value_label.config(text=f"{value:.2f}")
    
    def update_char_count(self, event=None):
        """文字数カウントを更新"""
        content = self.prompt_text.get(1.0, tk.END).strip()
        count = len(content)
        self.char_count_label.config(text=f"文字数: {count:,}")
    
    def show_progress(self, show=True):
        """プログレスバーの表示/非表示"""
        if show:
            self.progress.pack(fill=tk.X, pady=(0, 10), before=self.root.children[list(self.root.children.keys())[0]].children[list(self.root.children[list(self.root.children.keys())[0]].children.keys())[2]])
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress.pack_forget()
    
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
        
        status_text = f"📡 API Server: {self.api_url}"
        if model_names:
            status_text += f" ({len(model_names)} models available)"
        else:
            status_text += " (no models)"
        
        self.status_label.config(text=status_text)
    
    def send_request(self):
        """APIリクエストを送信"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showwarning("⚠️ 入力確認", "プロンプトを入力してください")
            return
        
        # ボタンを無効化とプログレスバー表示
        self.send_button.config(state=tk.DISABLED, text="📡 送信中...")
        self.show_progress(True)
        
        # レスポンスエリアをクリア
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, "🤔 AIが思考中です...\n\n✨ しばらくお待ちください")
        self.response_text.config(state=tk.DISABLED)
        
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
                    error_msg = f"❌ API エラー {response.status_code}\n\n{response.text}"
                    self.root.after(0, lambda: self.update_response_ui(error_msg, response_time, False))
                    
            except requests.exceptions.Timeout:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                error_msg = "⏰ タイムアウトエラー\n\nリクエストがタイムアウトしました。\nサーバーが応答していない可能性があります。"
                self.root.after(0, lambda: self.update_response_ui(error_msg, response_time, False))
            except requests.exceptions.ConnectionError:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                error_msg = "🔌 接続エラー\n\nAPIサーバーに接続できません。\nサーバーが起動しているか確認してください。"
                self.root.after(0, lambda: self.update_response_ui(error_msg, response_time, False))
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                error_msg = f"❌ リクエストエラー\n\n{str(e)}"
                self.root.after(0, lambda: self.update_response_ui(error_msg, response_time, False))
        
        threading.Thread(target=send_async, daemon=True).start()
    
    def update_response_ui(self, response_text, response_time, is_success):
        """レスポンスUIを更新"""
        # プログレスバーを非表示
        self.show_progress(False)
        
        # レスポンス表示を更新
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        
        if is_success:
            # 成功時は普通のテキスト
            self.response_text.insert(tk.END, response_text)
        else:
            # エラー時は強調表示
            self.response_text.insert(tk.END, response_text)
            # エラーテキストを赤色に（簡易的）
            self.response_text.tag_add("error", "1.0", tk.END)
            self.response_text.tag_config("error", foreground=self.colors['accent'])
        
        self.response_text.config(state=tk.DISABLED)
        
        # ボタンを再有効化
        self.send_button.config(state=tk.NORMAL, text="🚀 送信")
        
        # レスポンス時間を表示
        if is_success:
            if response_time < 1000:
                time_text = f"⚡ {response_time:.0f}ms"
                time_color = self.colors['success']
            elif response_time < 5000:
                time_text = f"⏱️ {response_time/1000:.1f}s"
                time_color = self.colors['warning']
            else:
                time_text = f"🐌 {response_time/1000:.1f}s"
                time_color = self.colors['accent']
        else:
            time_text = f"❌ {response_time:.0f}ms"
            time_color = self.colors['accent']
            
        self.response_time_label.config(text=time_text, foreground=time_color)
    
    def copy_response(self):
        """レスポンスをクリップボードにコピー"""
        response_content = self.response_text.get(1.0, tk.END).strip()
        if response_content:
            try:
                pyperclip.copy(response_content)
                # 成功メッセージをより控えめに
                self.status_label.config(text="📋 レスポンスをコピーしました")
                # 3秒後に元のステータスに戻す
                self.root.after(3000, lambda: self.status_label.config(
                    text=f"📡 API Server: {self.api_url}"))
            except Exception as e:
                messagebox.showerror("❌ コピーエラー", f"コピーに失敗しました:\n{str(e)}")
        else:
            messagebox.showwarning("⚠️ コピー確認", "コピーするレスポンスがありません")
    
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
            
            self.history_count_label.config(text=f"履歴: {len(history)}件")
            
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
                self.status_label.config(text="📋 プロンプトをコピーしました")
                self.root.after(3000, lambda: self.status_label.config(
                    text=f"📡 API Server: {self.api_url}"))
            except Exception as e:
                messagebox.showerror("❌ コピーエラー", f"コピーに失敗しました:\n{str(e)}")
    
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
                self.status_label.config(text="📋 回答をコピーしました")
                self.root.after(3000, lambda: self.status_label.config(
                    text=f"📡 API Server: {self.api_url}"))
            except Exception as e:
                messagebox.showerror("❌ コピーエラー", f"コピーに失敗しました:\n{str(e)}")
        else:
            messagebox.showwarning("⚠️ コピー確認", "コピーする回答がありません")
    
    def delete_history_item(self):
        """履歴項目を削除"""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        
        if messagebox.askyesno("🗑️ 削除確認", 
                              "この履歴項目を削除しますか？\n\nこの操作は取り消せません。",
                              icon="warning"):
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
                self.status_label.config(text="🗑️ 履歴項目を削除しました")
                self.root.after(3000, lambda: self.status_label.config(
                    text=f"📡 API Server: {self.api_url}"))
            except Exception as e:
                messagebox.showerror("❌ 削除エラー", f"削除に失敗しました:\n{str(e)}")
    
    def clear_all_history(self):
        """全ての履歴を削除"""
        if messagebox.askyesno("🗑️ 全削除確認", 
                              "すべての履歴を削除しますか？\n\n⚠️ この操作は取り消せません。",
                              icon="warning"):
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
                self.status_label.config(text=f"🗑️ {deleted_count}件の履歴を削除しました")
                self.root.after(3000, lambda: self.status_label.config(
                    text=f"📡 API Server: {self.api_url}"))
            except Exception as e:
                messagebox.showerror("❌ 削除エラー", f"削除に失敗しました:\n{str(e)}")
    
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
        messagebox.showerror("❌ エラー", message)
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
        print("=" * 70)
        print("🚀 LM Studio GUI アプリケーション起動中...")
        print(f"📱 Version: 20250527.1244")
        print("💡 モダンなUIデザインで快適な体験をお届けします")
        print("=" * 70)
        
        root = tk.Tk()
        
        # Windows DPI対応
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        app = LMStudioGUI(root)
        
        print("✅ GUI初期化完了 - アプリケーションを開始します")
        root.mainloop()
        
    except ImportError as e:
        if "pyperclip" in str(e):
            print("❌ 必要なライブラリが見つかりません")
            print("💡 以下のコマンドでインストールしてください:")
            print("   pip install pyperclip")
        else:
            print(f"❌ インポートエラー: {e}")
            print("💡 必要なライブラリをインストールしてください")
    except Exception as e:
        print(f"❌ アプリケーションエラー: {e}")
        print("💡 問題が解決しない場合は、設定ファイルを確認してください")

if __name__ == "__main__":
    main() 
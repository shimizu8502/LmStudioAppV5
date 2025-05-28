/** @format */

// DOM要素
const modelSelect = document.getElementById("model-select");
const refreshModelsBtn = document.getElementById("refresh-models");
const temperatureSlider = document.getElementById("temperature");
const temperatureValue = document.getElementById("temperature-value");
const maxTokensInput = document.getElementById("max-tokens");
const apiTypeRadios = document.getElementsByName("api-type");
const promptInput = document.getElementById("prompt-input");
const sendButton = document.getElementById("send-button");
const clearButton = document.getElementById("clear-button");
const responseOutput = document.getElementById("response-output");
const statusBar = document.getElementById("status-bar");
const promptHistoryList = document.getElementById("prompt-history-list");
const clearHistoryButton = document.getElementById("clear-history-button");
const copyResponseBtn = document.getElementById("copy-response-btn");
const clientIpDisplay = document.getElementById("client-ip-address");

// 履歴データの構造
let promptHistory = [];

// 初期化
document.addEventListener("DOMContentLoaded", () => {
  // モデル一覧を取得
  fetchModels();

  // Temperature値の表示を更新
  temperatureSlider.addEventListener("input", () => {
    temperatureValue.textContent = temperatureSlider.value;
  });

  // プロンプトステータス表示用の要素を作成
  createPromptStatus();

  // 履歴を読み込む
  loadPromptHistory();

  // クライアント情報を読み込む
  loadClientInfo();

  // 履歴関連のイベントリスナーを設定
  clearHistoryButton.addEventListener("click", clearPromptHistory);
  
  // コピーボタンのイベントリスナーを設定
  copyResponseBtn.addEventListener("click", () => copyToClipboard(responseOutput.textContent, copyResponseBtn));
  
  // 初期フォーカス
  promptInput.focus();
});

// クライアント情報をサーバーから読み込む
function loadClientInfo() {
  fetch("/api/client-info")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      clientIpDisplay.textContent = data.client_ip;
      clientIpDisplay.title = `接続時刻: ${new Date(data.timestamp).toLocaleString()}`;
    })
    .catch((error) => {
      console.error("クライアント情報の取得に失敗しました:", error);
      clientIpDisplay.textContent = "取得失敗";
    });
}

// 履歴をサーバーから読み込む
function loadPromptHistory() {
  setStatus("📚 履歴を読み込み中...");

  fetch("/api/prompt-history")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      promptHistory = data.history || [];
      renderPromptHistory();
      
      // クライアントIPも更新
      if (data.client_ip) {
        clientIpDisplay.textContent = data.client_ip;
      }
      
      setStatus(`✅ 履歴を読み込みました (${promptHistory.length}件) - IP: ${data.client_ip || '不明'}`);
    })
    .catch((error) => {
      console.error("履歴の読み込みに失敗しました:", error);
      setStatus(`❌ 履歴の読み込みに失敗: ${error.message}`);
    });
}

// 日時をフォーマットする関数
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMinutes < 1) {
    return "たった今";
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分前`;
  } else if (diffHours < 24) {
    return `${diffHours}時間前`;
  } else if (diffDays < 7) {
    return `${diffDays}日前`;
  } else {
    return date.toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}

// プロンプトの文字数を制限する関数
function truncateText(text, maxLength = 150) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

// 履歴を画面に表示
function renderPromptHistory() {
  promptHistoryList.innerHTML = "";

  if (promptHistory.length === 0) {
    const emptyMessage = document.createElement("div");
    emptyMessage.className = "history-empty";
    emptyMessage.innerHTML = `
      <div style="font-size: 48px; margin-bottom: 10px;">📝</div>
      <div>プロンプト履歴はまだありません</div>
      <div style="font-size: 12px; margin-top: 5px; color: #999;">
        最初のプロンプトを送信すると、ここに履歴が表示されます
      </div>
    `;
    promptHistoryList.appendChild(emptyMessage);
    return;
  }

  promptHistory.forEach((item, index) => {
    const historyItem = document.createElement("div");
    historyItem.className = "history-item";
    historyItem.dataset.id = item.id;

    // ヘッダー部分（API タイプとタイムスタンプ）
    const header = document.createElement("div");
    header.className = "history-item-header";

    const apiTypeBadge = document.createElement("span");
    apiTypeBadge.className = `api-type-badge ${item.api_type === "text" ? "text-type" : ""}`;
    apiTypeBadge.innerHTML = item.api_type === "chat" ? "💬 チャット" : "📝 テキスト";

    const timestamp = document.createElement("div");
    timestamp.className = "history-timestamp";
    timestamp.textContent = formatTimestamp(item.timestamp);

    header.appendChild(apiTypeBadge);
    header.appendChild(timestamp);

    // プロンプトプレビュー
    const promptPreview = document.createElement("div");
    promptPreview.className = "prompt-preview";
    const truncatedPrompt = truncateText(item.prompt);
    promptPreview.innerHTML = `<strong>質問:</strong> ${truncatedPrompt}`;
    
    // 回答プレビューを追加
    const responsePreview = document.createElement("div");
    responsePreview.className = "response-preview";
    
    const responseHeader = document.createElement("div");
    responseHeader.className = "response-header";
    responseHeader.style.display = "flex";
    responseHeader.style.justifyContent = "space-between";
    responseHeader.style.alignItems = "center";
    
    const responseContent = document.createElement("div");
    responseContent.className = "response-content";
    
    if (item.response) {
      const truncatedResponse = truncateText(item.response, 100);
      responseContent.innerHTML = `<strong>回答:</strong> ${truncatedResponse}`;
      
      // 回答のコピーボタンを追加
      const copyBtn = document.createElement("button");
      copyBtn.className = "copy-btn copy-btn-small";
      copyBtn.innerHTML = "📋";
      copyBtn.title = "回答をコピー";
      copyBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        copyToClipboard(item.response, copyBtn);
      });
      responseHeader.appendChild(copyBtn);
    } else {
      responseContent.innerHTML = `<strong>回答:</strong> <em style="color: #999;">なし</em>`;
    }
    
    responsePreview.appendChild(responseHeader);
    responsePreview.appendChild(responseContent);
    
    // クリックで展開/折りたたみ
    promptPreview.addEventListener("click", () => {
      if (promptPreview.classList.contains("expanded")) {
        promptPreview.innerHTML = `<strong>質問:</strong> ${truncatedPrompt}`;
        promptPreview.classList.remove("expanded");
        if (item.response) {
          const truncatedResponse = truncateText(item.response, 100);
          responseContent.innerHTML = `<strong>回答:</strong> ${truncatedResponse}`;
        }
        responsePreview.classList.remove("expanded");
      } else {
        promptPreview.innerHTML = `<strong>質問:</strong> ${item.prompt}`;
        promptPreview.classList.add("expanded");
        if (item.response) {
          responseContent.innerHTML = `<strong>回答:</strong> ${item.response}`;
        }
        responsePreview.classList.add("expanded");
      }
    });

    // 回答もクリックで展開/折りたたみ
    responseContent.addEventListener("click", () => {
      if (responsePreview.classList.contains("expanded")) {
        if (item.response) {
          const truncatedResponse = truncateText(item.response, 100);
          responseContent.innerHTML = `<strong>回答:</strong> ${truncatedResponse}`;
        }
        responsePreview.classList.remove("expanded");
        promptPreview.innerHTML = `<strong>質問:</strong> ${truncatedPrompt}`;
        promptPreview.classList.remove("expanded");
      } else {
        if (item.response) {
          responseContent.innerHTML = `<strong>回答:</strong> ${item.response}`;
        }
        responsePreview.classList.add("expanded");
        promptPreview.innerHTML = `<strong>質問:</strong> ${item.prompt}`;
        promptPreview.classList.add("expanded");
      }
    });

    // もし切り詰められている場合は、展開可能であることを示す
    if (item.prompt.length > 150 || (item.response && item.response.length > 100)) {
      promptPreview.style.cursor = "pointer";
      responseContent.style.cursor = "pointer";
      promptPreview.title = "クリックして全文を表示";
      responseContent.title = "クリックして全文を表示";
    }

    // コントロールボタン
    const controls = document.createElement("div");
    controls.className = "history-item-controls";

    const useButton = document.createElement("button");
    useButton.className = "use-prompt-btn";
    useButton.innerHTML = "✅ 使用";
    useButton.title = "このプロンプトを入力エリアに設定";
    useButton.addEventListener("click", () => usePromptFromHistory(item));

    const editButton = document.createElement("button");
    editButton.className = "edit-prompt-btn";
    editButton.innerHTML = "✏️ 編集";
    editButton.title = "このプロンプトを編集";
    editButton.addEventListener("click", () => editPromptFromHistory(item));

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-prompt-btn";
    deleteButton.innerHTML = "🗑️ 削除";
    deleteButton.title = "この履歴を削除";
    deleteButton.addEventListener("click", () => {
      if (confirm("この履歴を削除しますか？")) {
        deletePromptFromHistory(item.id);
      }
    });

    // 要素を組み立てる
    controls.appendChild(useButton);
    controls.appendChild(editButton);
    controls.appendChild(deleteButton);

    historyItem.appendChild(header);
    historyItem.appendChild(promptPreview);
    historyItem.appendChild(responsePreview);
    historyItem.appendChild(controls);

    promptHistoryList.appendChild(historyItem);
  });
}

// 履歴からプロンプトを使用
function usePromptFromHistory(historyItem) {
  // 現在の入力内容がある場合は確認
  if (promptInput.value.trim() && !confirm("現在の入力内容を破棄して、履歴のプロンプトを使用しますか？")) {
    return;
  }

  promptInput.value = historyItem.prompt;

  // APIタイプを設定
  for (const radio of apiTypeRadios) {
    if (radio.value === historyItem.api_type) {
      radio.checked = true;
      break;
    }
  }

  // 回答がある場合は回答エリアにも表示
  if (historyItem.response) {
    responseOutput.textContent = historyItem.response;
    copyResponseBtn.style.display = "block";
  } else {
    responseOutput.textContent = "";
    copyResponseBtn.style.display = "none";
  }

  promptInput.focus();
  
  // スクロールして入力エリアを表示
  promptInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
  
  setStatus(`📋 履歴からプロンプトと回答を読み込みました`);
}

// 履歴からプロンプトを編集
function editPromptFromHistory(historyItem) {
  // 編集中のプロンプトが既にある場合は確認
  if (promptInput.value.trim() && !confirm("現在の入力内容を破棄して、履歴のプロンプトを編集しますか？")) {
    return;
  }

  // プロンプト入力欄に設定
  promptInput.value = historyItem.prompt;

  // APIタイプを設定
  for (const radio of apiTypeRadios) {
    if (radio.value === historyItem.api_type) {
      radio.checked = true;
      break;
    }
  }

  // 回答エリアもクリア
  responseOutput.textContent = "";
  copyResponseBtn.style.display = "none";

  promptInput.focus();
  promptInput.setSelectionRange(promptInput.value.length, promptInput.value.length);
  
  // スクロールして入力エリアを表示
  promptInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
  
  setStatus(`✏️ プロンプトを編集モードで読み込みました（元の履歴は保持されます）`);
}

// 履歴からプロンプトを削除
function deletePromptFromHistory(id) {
  setStatus("🗑️ 履歴を削除中...");

  fetch(`/api/prompt-history/${id}`, {
    method: "DELETE",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return response.json();
    })
    .then(() => {
      // ローカルのリストからも削除
      const index = promptHistory.findIndex((item) => item.id === id);
      if (index !== -1) {
        promptHistory.splice(index, 1);
      }
      renderPromptHistory();
      setStatus(`✅ 履歴から削除しました (残り${promptHistory.length}件)`);
    })
    .catch((error) => {
      console.error("履歴の削除に失敗しました:", error);
      setStatus(`❌ 履歴の削除に失敗: ${error.message}`);
    });
}

// 履歴をすべてクリア
function clearPromptHistory() {
  if (confirm("⚠️ プロンプト履歴をすべて削除しますか？\nこの操作は元に戻せません。")) {
    setStatus("🗑️ 履歴をクリア中...");

    fetch("/api/prompt-history", {
      method: "DELETE",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        promptHistory = [];
        renderPromptHistory();
        setStatus(`✅ プロンプト履歴をクリアしました - IP: ${data.client_ip || '不明'}`);
      })
      .catch((error) => {
        console.error("履歴のクリアに失敗しました:", error);
        setStatus(`❌ 履歴のクリアに失敗: ${error.message}`);
      });
  }
}

// プロンプトステータス表示用の要素を作成する関数
function createPromptStatus() {
  const promptSection = document.querySelector(".input-section h2");
  const statusSpan = document.createElement("span");
  statusSpan.id = "prompt-status";
  statusSpan.style.marginLeft = "10px";
  statusSpan.style.fontSize = "0.9em";
  statusSpan.style.display = "none";
  promptSection.appendChild(statusSpan);
}

// プロンプトステータスを表示する関数
function setPromptStatus(message, isProcessing = false) {
  const statusSpan = document.getElementById("prompt-status");
  if (statusSpan) {
    statusSpan.textContent = message;
    statusSpan.style.color = isProcessing ? "#ff6b6b" : "#00b894";
    statusSpan.style.display = "inline";
  }
}

// プロンプトステータスを非表示にする関数
function hidePromptStatus() {
  const statusSpan = document.getElementById("prompt-status");
  if (statusSpan) {
    statusSpan.style.display = "none";
  }
}

// モデル一覧を取得する関数
function fetchModels() {
  setStatus("🔍 モデル一覧を取得中...");

  fetch("/api/models")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      // セレクトボックスをクリア
      modelSelect.innerHTML = '<option value="">モデルを選択してください</option>';

      // モデル一覧を追加
      const models = data.data || [];
      models.forEach((model) => {
        const option = document.createElement("option");
        option.value = model.id;
        option.textContent = model.id;
        modelSelect.appendChild(option);
      });

      if (models.length > 0) {
        setStatus(`✅ ${models.length}個のモデルが見つかりました`);
        // 最初のモデルを選択
        modelSelect.value = models[0].id;
      } else {
        setStatus("⚠️ モデルが見つかりませんでした");
      }
    })
    .catch((error) => {
      console.error("Error fetching models:", error);
      setStatus(`❌ エラー: ${error.message}`);
    });
}

// プロンプトを送信する関数
function sendPrompt() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("⚠️ プロンプトを入力してください");
    promptInput.focus();
    return;
  }

  const model = modelSelect.value;
  const temperature = parseFloat(temperatureSlider.value);
  const maxTokens = parseInt(maxTokensInput.value);

  // APIタイプを取得（chatまたはtext）
  let apiType = "chat";
  for (const radio of apiTypeRadios) {
    if (radio.checked) {
      apiType = radio.value;
      break;
    }
  }

  // リクエストデータ
  const requestData = {
    prompt: prompt,
    model: model,
    temperature: temperature,
    max_tokens: maxTokens,
  };

  // 送信前の準備
  const startTime = performance.now(); // レスポンス時間測定開始
  setStatus("🚀 リクエスト送信中...");
  setPromptStatus("🔄 処理中", true);
  sendButton.disabled = true;
  sendButton.textContent = "⏳ 処理中...";
  sendButton.classList.add("processing");
  responseOutput.textContent = "🤖 AIが回答を生成中です...\n\n⚡ 高速化機能で処理を最適化中...";
  responseOutput.classList.add("processing");

  // APIエンドポイント
  const endpoint = apiType === "chat" ? "/api/chat" : "/api/text";

  // フェッチリクエスト
  fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestData),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((errData) => {
          throw new Error(`${errData.error || "APIエラー"} ${errData.details || ""}`);
        });
      }
      return response.json();
    })
    .then((data) => {
      // レスポンスを処理
      let result = "";

      if (apiType === "chat") {
        // チャット完了APIの場合
        result = data.choices?.[0]?.message?.content || "レスポンスが空です";
      } else {
        // テキスト完了APIの場合
        result = data.choices?.[0]?.text || "レスポンスが空です";
      }

      responseOutput.textContent = result;
      copyResponseBtn.style.display = result ? "block" : "none";
      
      // レスポンス時間を計算して表示
      const endTime = performance.now();
      const responseTime = ((endTime - startTime) / 1000).toFixed(2);
      setStatus(`✅ 回答の生成が完了しました（${responseTime}秒）`);
      setPromptStatus("✅ 完了", false);

      // 送信後に履歴を再読み込み（非同期で並行処理）
      loadPromptHistory();
      
      // 回答エリアにスクロール
      responseOutput.scrollIntoView({ behavior: 'smooth', block: 'start' });
    })
    .catch((error) => {
      console.error("Error sending prompt:", error);
      
      // エラー時もレスポンス時間を計算
      const endTime = performance.now();
      const responseTime = ((endTime - startTime) / 1000).toFixed(2);
      
      responseOutput.textContent = `❌ エラーが発生しました: ${error.message}\n\n🔧 以下を確認してください:\n• LM Studio APIサーバーが起動しているか\n• ネットワーク接続が正常か\n• 選択したモデルが利用可能か\n\n⏱️ 処理時間: ${responseTime}秒`;
      setStatus(`❌ エラー: ${error.message}（${responseTime}秒）`);
      setPromptStatus("❌ エラー", false);
    })
    .finally(() => {
      sendButton.disabled = false;
      sendButton.textContent = "🚀 送信";
      sendButton.classList.remove("processing");
      responseOutput.classList.remove("processing");
    });
}

// プロンプトをクリアする関数
function clearPrompt() {
  if (promptInput.value.trim() && !confirm("入力したプロンプトを削除しますか？")) {
    return;
  }
  
  promptInput.value = "";
  responseOutput.textContent = "";
  copyResponseBtn.style.display = "none";
  setStatus("🗑️ プロンプトをクリアしました");
  hidePromptStatus();
  promptInput.focus();
}

// ステータスバーを更新する関数
function setStatus(message) {
  statusBar.textContent = message;
}

// クリップボードにコピーする関数
async function copyToClipboard(text, button) {
  if (!text || text.trim() === "") {
    setStatus("⚠️ コピーするテキストがありません");
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    
    // ボタンの表示を一時的に変更
    const originalText = button.innerHTML;
    const originalClass = button.className;
    
    button.innerHTML = "✅ コピー完了";
    button.classList.add("copied");
    
    setStatus(`📋 クリップボードにコピーしました (${text.length}文字)`);
    
    // 2秒後に元に戻す
    setTimeout(() => {
      button.innerHTML = originalText;
      button.className = originalClass;
    }, 2000);
    
  } catch (err) {
    console.error("コピーに失敗しました:", err);
    
    // フォールバック: 古いブラウザ用
    try {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.left = "-999999px";
      textArea.style.top = "-999999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      
      setStatus(`📋 クリップボードにコピーしました (${text.length}文字)`);
      
      // ボタンの表示を一時的に変更
      const originalText = button.innerHTML;
      const originalClass = button.className;
      
      button.innerHTML = "✅ コピー完了";
      button.classList.add("copied");
      
      setTimeout(() => {
        button.innerHTML = originalText;
        button.className = originalClass;
      }, 2000);
      
    } catch (fallbackErr) {
      console.error("フォールバックコピーも失敗しました:", fallbackErr);
      setStatus("❌ コピーに失敗しました");
    }
  }
}

// イベントリスナー
refreshModelsBtn.addEventListener("click", fetchModels);
sendButton.addEventListener("click", sendPrompt);
clearButton.addEventListener("click", clearPrompt);

// キーボード操作の処理
promptInput.addEventListener("keydown", (e) => {
  // Enterキーでの送信を無効化（送信ボタンのみ有効）
  // if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey) {
  //   e.preventDefault();
  //   sendPrompt();
  // }
  // Shift + Enterで改行（デフォルト動作をそのまま実行）
  if (e.key === "Enter" && e.shiftKey) {
    // デフォルトの改行動作を維持（preventDefault()を呼び出さない）
    setStatus("🔄 改行を追加しました");
  }
  // 通常のEnterキーでも改行のみ（送信しない）
  else if (e.key === "Enter") {
    // デフォルトの改行動作を維持
    setStatus("📝 改行しました（送信は送信ボタンを押してください）");
  }
});

// プロンプト入力時の文字数カウント（オプション）
promptInput.addEventListener("input", () => {
  const charCount = promptInput.value.length;
  if (charCount > 0) {
    setStatus(`✍️ ${charCount}文字入力中...`);
  } else {
    setStatus("✅ 準備完了");
  }
});

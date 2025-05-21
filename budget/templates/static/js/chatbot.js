document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendMessage = document.getElementById('send-message');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotReset = document.getElementById('chatbot-reset'); // リセットボタン
    const newThreadButton = document.getElementById('new-thread'); // 新しいスレッド作成ボタン
    const threadListElement = document.getElementById('thread-list'); // スレッドリスト
    let threadId = getThreadIdFromUrl(); // 現在のスレッドIDを取得

    // 送信ボタンのクリックイベントリスナー
    sendMessage.addEventListener('click', handleSendMessage);

    // Enterキーでメッセージを送信するためのイベントリスナー
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });

    // リセットボタンのイベントリスナー
    if (chatbotReset) {
        chatbotReset.addEventListener('click', resetChatHistory);
    }

    // 新しいスレッド作成ボタンのイベントリスナー
    if (newThreadButton) {
        newThreadButton.addEventListener('click', createNewThreadAndRedirect);
    }

    // スレッド削除ボタンのイベントリスナー
    threadListElement.addEventListener('click', (e) => {
        if (e.target.classList.contains('delete-thread-btn')) {
            const threadIdToDelete = e.target.getAttribute('data-thread-id');

            if (confirm('このスレッドを削除しますか？')) {
                deleteThread(threadIdToDelete);
            }
        }
    });

    // スレッドのタイトル変更ボタンのイベントリスナー
    threadListElement.addEventListener('click', (e) => {
        if (e.target.classList.contains('rename-thread-btn')) {
            const threadId = e.target.getAttribute('data-thread-id');
            const newTitle = prompt('新しいタイトルを入力してください:');
            if (newTitle) {
                renameThread(threadId, newTitle);
            }
        }
    });

// チャットメッセージ関係
    // メッセージ送信時にスレッドが未選択なら新しいスレッドを作成
    async function handleSendMessage() {
        const message = userInput.value.trim(); // 入力されたメッセージを取得
        if (!message) return; // メッセージが空の場合は終了
    
        if (!threadId) {
            // スレッドが未選択の場合、新しいスレッドを作成
            const newThreadId = await createNewThread(); // 新しいスレッド作成を待機
            threadId = newThreadId; // スレッドIDを設定
            await sendUserMessage(message); // メッセージを送信（完了を待つ）
            window.location.href = `/chatbot/threads/${newThreadId}/`; // 新スレッドページにリダイレクト
        } else {
            // 既存スレッドがある場合
            await sendUserMessage(message); // メッセージを送信（完了を待つ）
        }
    }
    

    // ユーザーメッセージを送信
    async function sendUserMessage(message) {
        addMessage('user-message', message); // メッセージを表示
        userInput.value = ''; // 入力フィールドをクリア
    
        if (threadId) {
            await fetchBotResponse(message); // ボットの応答を取得（完了を待つ）
        } else {
            await createNewThreadAndSendMessage(message); // 新しいスレッドを作成して送信
        }
    }
    

    async function sendUserMessageToThread(message, threadId) {
        const response = await fetch('/chat_api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ message: message, thread_id: threadId }),
        });
    
        const data = await response.json();
        addMessage('user-message', message); // ユーザーメッセージを追加
        addMessage('assistant-message', data.message); // ボット応答を追加
    }
    

    // ボットからの応答を取得
    async function fetchBotResponse(message) {
        const response = await fetch('/chat_api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ message: message, thread_id: threadId }),
        });
    
        if (!response.ok) {
            throw new Error('Failed to fetch bot response');
        }
    
        const data = await response.json();
        addMessage('assistant-message', data.message); // ボットの応答を追加
    }
    
    
    // メッセージをチャット画面に追加
    function addMessage(senderClass, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add(senderClass);
        messageElement.textContent = message;
        chatbotMessages.appendChild(messageElement);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight; // 自動スクロール
    }

// スレッド管理関係
    // 新しいスレッドを作成
    function createNewThread() {
        return fetch('/chatbot/threads/create/', {
            method: 'POST', // POSTメソッドを指定
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to create thread');
                }
                return response.json();
            })
            .then(data => {
                return data.thread_id;
            })
            .catch(error => {
                console.error('Error creating thread:', error);
                throw error;
            });
    }

    // 新しいスレッドを作成してメッセージを送信
    async function createNewThreadAndSendMessage(message) {
        const response = await fetch('/chatbot/threads/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({})
        });
    
        const data = await response.json();
        if (data.thread_id) {
            threadId = data.thread_id;
            await sendUserMessageToThread(message, threadId); // 完了を待機
        }
    }
    

    // 新しいスレッドを作成してリダイレクト
    function createNewThreadAndRedirect() {
        createNewThread().then((newThreadId) => {
            window.location.href = `/chatbot/threads/${newThreadId}/`;
        });
    }

    // スレッドを削除
    function deleteThread(threadIdToDelete) {
        fetch(`/chatbot/threads/${threadIdToDelete}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Failed to delete thread');
                }
                return response.json();
            })
            .then((data) => {
                if (data.status === 'success') {
                    const currentUrlThreadId = getThreadIdFromUrl();
                    if (currentUrlThreadId === threadIdToDelete) {
                        // 現在のスレッドが削除された場合
                        window.location.href = data.redirect_url;
                    } else {
                        refreshThreadList();
                    }
                } else {
                    console.error('Failed to delete thread:', data.message);
                }
            })
            .catch((error) => {
                console.error('Error deleting thread:', error);
            });
    }

    // スレッドタイトル変更関数
    function renameThread(threadId, newTitle) {
        fetch(`/chatbot/threads/${threadId}/rename/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ title: newTitle }),
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === 'success') {
                location.reload(); // ページをリロードして更新を反映
            } else {
                alert('タイトルの変更に失敗しました。');
            }
        })
        .catch((error) => {
            console.error('Error renaming thread:', error);
        });
    }

    function refreshThreadList() {
        fetch('/api/thread-list/')
        .then(response => response.json())
        .then(data => {
            const threadList = document.getElementById('thread-list');
            threadList.innerHTML = ''; // 現在のリストをクリア
            data.threads.forEach(thread => {
                const newThreadItem = document.createElement('li');
                newThreadItem.innerHTML = `
                    <a href="/chatbot/threads/${thread.id}/">${thread.title}</a>
                    <div class="dropdown">
                    <button class="btn dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                    </button>
                    <ul class="dropdown-menu">
                        <li>
                            <button class="dropdown-item rename-thread-btn" data-thread-id="${ thread.id }">タイトル変更</button>
                        </li>
                        <li>
                            <button class="dropdown-item delete-thread-btn" data-thread-id="${ thread.id }">削除</button>
                        </li>
                    </ul>
                </div> 
                `;
                threadList.appendChild(newThreadItem);
            });
        });
    }
    

// 履歴の管理関係
    // チャット履歴をリセット
    function resetChatHistory() {
        fetch('/api/reset-chat-history/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ thread_id: threadId }) // 現在のスレッドIDを送信
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Chat history cleared for the current thread.');
                    chatbotMessages.innerHTML = ''; // フロントエンド上の履歴をクリア
                } else {
                    console.error('Failed to clear chat history:', data.message);
                }
            })
            .catch(error => {
                console.error('Error resetting chat history:', error);
            });
    }

    // 現在のURLからスレッドIDを取得
    function getThreadIdFromUrl() {
        const urlParts = window.location.pathname.split('/');
        const threadIndex = urlParts.indexOf('threads');
        if (threadIndex !== -1 && urlParts[threadIndex + 1]) {
            return urlParts[threadIndex + 1];
        }
        return null;
    }

// ユーティリティ関係
    // CSRFトークンを取得するヘルパー関数
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});

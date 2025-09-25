document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const uploadBtn = document.getElementById('upload-btn');
    const imageUpload = document.getElementById('image-upload');
    const colorButtons = document.querySelectorAll('.color-btn');

    // 1. 텍스트 메시지 제출 이벤트
    messageForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const messageText = messageInput.value.trim();
        if (messageText) {
            appendMessage(messageText, 'user-message');
            messageInput.value = '';
            await fetchBotResponse('/api/chat/text', { message: messageText });
        }
    });

    // 2. 이미지 업로드 버튼 클릭 이벤트
    uploadBtn.addEventListener('click', () => imageUpload.click());

    // 이미지 파일 선택 이벤트
    imageUpload.addEventListener('change', async () => {
        const file = imageUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const imageElement = `<img src="${e.target.result}" alt="업로드 이미지">`;
                appendMessage(imageElement, 'user-message');
            };
            reader.readAsDataURL(file);

            const formData = new FormData();
            formData.append('image', file);
            await fetchBotResponse('/api/chat/image', formData);
            imageUpload.value = ''; // Reset input
        }
    });

    // 3. 색상 버튼 클릭 이벤트
    colorButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const color = button.dataset.color;
            const colorMessage = `${color.charAt(0).toUpperCase() + color.slice(1)} 색상을 선택했어요.`;
            appendMessage(colorMessage, 'user-message');
            await fetchBotResponse('/api/chat/color', { color: color });
        });
    });

    /**
     * 백엔드 API와 통신하여 봇의 응답을 가져오는 함수
     * @param {string} endpoint - API 엔드포인트
     * @param {object|FormData} body - 전송할 데이터
     */
    async function fetchBotResponse(endpoint, body) {
        appendMessage('Playlist를 찾고 있어요', 'bot-message', true);

        try {
            const isFormData = body instanceof FormData;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: isFormData ? {} : { 'Content-Type': 'application/json' },
                body: isFormData ? body : JSON.stringify(body),
            });

            removeTypingIndicator();

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '서버 응답에 문제가 발생했습니다.');
            }

            const data = await response.json();
            renderBotResponse(data);

        } catch (error) {
            removeTypingIndicator();
            appendMessage(`죄송합니다. 오류가 발생했어요: ${error.message}`, 'bot-message');
            console.error('Error:', error);
        }
    }

    /**
     * 서버로부터 받은 데이터를 채팅창에 렌더링하는 함수
     * @param {object} data - 서버 응답 JSON 데이터
     */
    function renderBotResponse(data) {
        let botReply = `<p><strong>${data.emotion}</strong>에 어울리는 플레이리스트를 추천해 드릴게요!</p><ul>`;
        data.recommended_songs.forEach(song => {
            botReply += `<li>🎵 ${song.artist} - ${song.title} 
                (<a href="${song.youtube_link}" target="_blank">듣기</a>)</li>`;
        });
        botReply += `</ul>`;
        appendMessage(botReply, 'bot-message');
    }
    
    /**
     * 채팅창에 메시지를 추가하는 함수
     * @param {string} text - 메시지 내용 (HTML 가능)
     * @param {string} className - 'user-message' 또는 'bot-message'
     * @param {boolean} isTyping - 로딩 인디케이터 여부
     */
    function appendMessage(text, className, isTyping = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', className);
        if (isTyping) {
            messageElement.classList.add('typing-indicator');
        }
        messageElement.innerHTML = `<p>${text}</p>`;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    /**
     * 로딩 인디케이터를 제거하는 함수
     */
    function removeTypingIndicator() {
        const indicator = chatBox.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
});
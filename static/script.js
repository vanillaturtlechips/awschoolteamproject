document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const uploadBtn = document.getElementById('upload-btn');
    const imageUpload = document.getElementById('image-upload');

    // 메시지 폼 제출 이벤트
    messageForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const messageText = messageInput.value.trim();
        if (messageText) {
            appendMessage(messageText, 'user-message');
            // 서버 대신 가짜 응답 함수 호출
            getFakeBotResponse();
            messageInput.value = '';
        }
    });

    // 이미지 업로드 버튼 클릭 이벤트
    uploadBtn.addEventListener('click', () => {
        imageUpload.click();
    });

    // 이미지 파일 선택 이벤트
    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const imageElement = `<img src="${e.target.result}" style="max-width: 100%; border-radius: 10px;">`;
                appendMessage(imageElement, 'user-message');
            };
            reader.readAsDataURL(file);

            // 서버 대신 가짜 응답 함수 호출
            getFakeBotResponse();
            imageUpload.value = '';
        }
    });

    /**
     * 서버가 없어도 봇이 응답하는 것처럼 보이게 하는 가짜 함수
     */
    function getFakeBotResponse() {
        appendMessage('Playlist를 찾고 있어요... 잠시만 기다려주세요!', 'bot-message', true);

        // 1.5초 후에 가짜 응답을 보여줌
        setTimeout(() => {
            removeTypingIndicator();
            const fakeReply = `요청하신内容에 맞는 플레이리스트입니다:<br>
                1. 아이유 - 밤편지 (<a href="#" onclick="return false;">듣기</a>)<br>
                2. 잔나비 - 주저하는 연인들을 위해 (<a href="#" onclick="return false;">듣기</a>)<br>
                3. 폴킴 - 모든 날, 모든 순간 (<a href="#" onclick="return false;">듣기</a>)`;
            appendMessage(fakeReply, 'bot-message');
        }, 1500);
    }

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

    function removeTypingIndicator() {
        const indicator = chatBox.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
});
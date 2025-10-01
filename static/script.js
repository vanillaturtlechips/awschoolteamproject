document.addEventListener('DOMContentLoaded', () => {
    // HTML에서 필요한 요소들을 가져옵니다.
    const chatBox = document.getElementById('chat-box');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const uploadBtn = document.getElementById('upload-btn');
    const imageUpload = document.getElementById('image-upload');
    const colorButtons = document.querySelectorAll('.color-btn');
    const attachmentPreview = document.getElementById('attachment-preview');

    // 사용자의 선택(색상, 이미지)을 임시로 저장할 변수들을 선언합니다.
    let selectedColor = null;
    let selectedImageFile = null;

    // 1. 색상 버튼 클릭 이벤트 처리
    colorButtons.forEach(button => {
        button.addEventListener('click', () => {
            const color = button.dataset.color;
            if (selectedColor === color) {
                selectedColor = null;
                button.classList.remove('selected');
            } else {
                colorButtons.forEach(btn => btn.classList.remove('selected'));
                selectedColor = color;
                button.classList.add('selected');
            }
        });
    });

    // 2. 이미지 업로드 버튼(+) 클릭 이벤트 처리
    uploadBtn.addEventListener('click', () => imageUpload.click());

    // 3. 이미지 파일이 선택되었을 때의 이벤트 처리
    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (file) {
            selectedImageFile = file;
            showAttachmentPreview(file);
        }
    });

    // 4. 전송(Send) 버튼 클릭 또는 Enter 키 입력 시 이벤트 처리
    messageForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const messageText = messageInput.value.trim();

        if (!messageText && !selectedColor && !selectedImageFile) {
            return;
        }

        // 채팅창에 사용자가 보낸 내용을 시각적으로 표시합니다.
        let userMessageHTML = '';
        if (selectedColor) {
            const colorBtn = document.querySelector(`.color-btn[data-color="${selectedColor}"]`);
            userMessageHTML += `<span class="color-tag" style="background-color: ${getComputedStyle(colorBtn).backgroundColor};"></span> `;
        }
        if (selectedImageFile) {
            userMessageHTML += '🖼️ ';
        }
        if (messageText) {
            userMessageHTML += messageText;
        }
        appendMessage(userMessageHTML, 'user-message');
        
        // 우선순위: 이미지 > 색상 > 텍스트 순으로 API 호출
        if (selectedImageFile) {
            await handleImageRequest();
        } else if (selectedColor) {
            await handleColorRequest();
        } else if (messageText) {
            await handleTextRequest(messageText);
        }

        resetInputs();
    });
    
    // 텍스트 요청 처리
    async function handleTextRequest(message) {
        const requestBody = { message: message };
        await fetchBotResponse('/api/chat/text', 'application/json', JSON.stringify(requestBody));
    }

    // 색상 요청 처리
    async function handleColorRequest() {
        const requestBody = { color: selectedColor };
        await fetchBotResponse('/api/chat/color', 'application/json', JSON.stringify(requestBody));
    }

    // 이미지 요청 처리
    async function handleImageRequest() {
        const formData = new FormData();
        formData.append('image', selectedImageFile, selectedImageFile.name);
        await fetchBotResponse('/api/chat/image', null, formData);
    }
    
    // 첨부된 이미지의 미리보기를 화면에 보여주는 함수
    function showAttachmentPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            attachmentPreview.style.display = 'flex';
            attachmentPreview.innerHTML = `
                <img src="${e.target.result}" alt="preview">
                <p>${file.name}</p>
                <button id="remove-attachment">&times;</button>
            `;
            document.getElementById('remove-attachment').addEventListener('click', resetImageAttachment);
        };
        reader.readAsDataURL(file);
    }

    // 이미지 첨부 상태를 초기화하는 함수
    function resetImageAttachment() {
        selectedImageFile = null;
        imageUpload.value = '';
        attachmentPreview.innerHTML = '';
        attachmentPreview.style.display = 'none';
    }

    // 모든 입력을 초기 상태로 되돌리는 함수
    function resetInputs() {
        messageInput.value = '';
        colorButtons.forEach(btn => btn.classList.remove('selected'));
        selectedColor = null;
        resetImageAttachment();
    }

    // 백엔드 서버와 통신하는 함수 (수정됨)
    async function fetchBotResponse(endpoint, contentType, body) {
        // EC2 서버의 8000번 포트로 요청
        const backendUrl = `http://playlist-bot-alb-864387607.ap-northeast-2.elb.amazonaws.com${endpoint}`;

        appendMessage('Playlist를 찾고 있어요...', 'bot-message', true);
        try {
            const headers = {};
            if (contentType) {
                headers['Content-Type'] = contentType;
            }

            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: headers,
                body: body,
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

    // 서버로부터 받은 추천 결과를 채팅창에 예쁘게 그려주는 함수
    function renderBotResponse(data) {
        let botReply = `<p><strong>${data.emotion}</strong>에 어울리는 플레이리스트를 추천해 드릴게요!</p><ul>`;
        data.recommended_songs.forEach(song => {
            botReply += `<li>🎵 ${song.artist} - ${song.title} 
                (<a href="${song.youtube_link}" target="_blank" rel="noopener noreferrer">듣기</a>)</li>`;
        });
        botReply += `</ul>`;
        appendMessage(botReply, 'bot-message');
    }

    // 채팅창에 새로운 메시지 요소를 추가하는 함수
    function appendMessage(html, className, isTyping = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', className);
        if (isTyping) {
            messageElement.classList.add('typing-indicator');
        }
        messageElement.innerHTML = html;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // "입력 중..." 메시지를 제거하는 함수
    function removeTypingIndicator() {
        const indicator = chatBox.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
});
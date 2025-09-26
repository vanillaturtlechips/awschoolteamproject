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
    //   - 요청을 바로 보내지 않고, 선택한 색상을 selectedColor 변수에 저장합니다.
    //   - 선택된 버튼에는 'selected' 클래스를 추가하여 시각적으로 표시합니다.
    colorButtons.forEach(button => {
        button.addEventListener('click', () => {
            const color = button.dataset.color;
            if (selectedColor === color) {
                // 이미 선택된 색상을 다시 누르면 선택을 해제합니다.
                selectedColor = null;
                button.classList.remove('selected');
            } else {
                // 다른 색상을 선택하면, 이전에 선택된 것은 해제하고 새로 선택합니다.
                colorButtons.forEach(btn => btn.classList.remove('selected'));
                selectedColor = color;
                button.classList.add('selected');
            }
        });
    });

    // 2. 이미지 업로드 버튼(+) 클릭 이벤트 처리
    //   - 숨겨진 파일 입력창을 클릭하여 파일 선택 창을 띄웁니다.
    uploadBtn.addEventListener('click', () => imageUpload.click());

    // 3. 이미지 파일이 선택되었을 때의 이벤트 처리
    //   - 요청을 바로 보내지 않고, 선택한 파일을 selectedImageFile 변수에 저장합니다.
    //   - 사용자에게 어떤 파일이 첨부되었는지 보여주는 미리보기를 생성합니다.
    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (file) {
            selectedImageFile = file;
            showAttachmentPreview(file);
        }
    });

    // 4. 전송(Send) 버튼 클릭 또는 Enter 키 입력 시 이벤트 처리 (가장 핵심적인 부분)
    //   - 지금까지 저장된 모든 정보(텍스트, 색상, 이미지)를 한 번에 모아서 서버로 전송합니다.
    messageForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // 폼의 기본 제출 동작(페이지 새로고침)을 막습니다.
        const messageText = messageInput.value.trim();

        // 텍스트, 색상, 이미지 중 아무것도 입력/선택되지 않았으면 아무 작업도 하지 않습니다.
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
        
        // 서버에 보낼 데이터를 FormData 객체에 담습니다.
        // FormData는 텍스트와 파일을 함께 보낼 때 유용합니다.
        const formData = new FormData();
        if (messageText) formData.append('text', messageText);
        if (selectedColor) formData.append('color', selectedColor);
        if (selectedImageFile) formData.append('image', selectedImageFile, selectedImageFile.name);

        // 전송 후, 모든 입력창과 선택 상태를 깨끗하게 초기화합니다.
        resetInputs();

        // 모든 데이터가 담긴 FormData를 백엔드 API로 전송합니다.
        await fetchBotResponse('/api/chat/combined', formData);
    });
    
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
            // 미리보기 옆의 'x' 버튼을 누르면 첨부를 취소하는 이벤트를 연결합니다.
            document.getElementById('remove-attachment').addEventListener('click', resetImageAttachment);
        };
        reader.readAsDataURL(file);
    }

    // 이미지 첨부 상태를 초기화하는 함수
    function resetImageAttachment() {
        selectedImageFile = null;
        imageUpload.value = ''; // 파일 입력창의 값을 비워야 같은 파일을 다시 선택할 수 있습니다.
        attachmentPreview.innerHTML = '';
        attachmentPreview.style.display = 'none';
    }

    // 모든 입력(텍스트, 색상, 이미지)을 초기 상태로 되돌리는 함수
    function resetInputs() {
        messageInput.value = '';
        colorButtons.forEach(btn => btn.classList.remove('selected'));
        selectedColor = null;
        resetImageAttachment();
    }

    // 백엔드 서버와 통신하는 함수
    async function fetchBotResponse(endpoint, body) {
        // [수정됨] EC2 서버의 공인 IP 주소를 여기에 직접 입력합니다.
        const backendUrl = `http://3.36.74.0${endpoint}`;

        appendMessage('Playlist를 찾고 있어요...', 'bot-message', true);
        try {
            const response = await fetch(backendUrl, {
                method: 'POST',
                body: body, // FormData를 보낼 때는 Content-Type 헤더를 지정할 필요가 없습니다. 브라우저가 자동으로 처리합니다.
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
        messageElement.innerHTML = html; // 텍스트 대신 HTML을 직접 삽입
        chatBox.appendChild(messageElement);
        // 항상 가장 아래로 스크롤하여 최신 메시지를 보여줍니다.
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
document.addEventListener('DOMContentLoaded', () => {
  setupPasswordToggles();
  setupLoginForm();
  setupRegisterForm();
  setupChatInterface();
  setupAnimation();
});

function setupPasswordToggles() {
  document.querySelectorAll('.toggle-password').forEach((button) => {
    button.addEventListener('click', () => {
      const input = button.parentElement.querySelector('input');
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      button.textContent = isPassword ? 'Hide' : 'Show';
    });
  });
}

function setupAnimation() {
  const scene = document.querySelector('.auth-scene');
  const person = document.querySelector('.person-figure');
  const bag = document.querySelector('.bag');
  const card = document.querySelector('.login-card-wrapper');

  if (!scene || !person || !bag || !card) return;

  scene.classList.add('cinematic');

  setTimeout(() => {
    bag.classList.add('drop');
  }, 1800);

  setTimeout(() => {
    person.classList.add('reveal');
  }, 2600);

  setTimeout(() => {
    person.classList.add('remote-press');
    bag.classList.add('unlocking');
  }, 3400);

  setTimeout(() => {
    bag.classList.add('open');
  }, 4300);

  setTimeout(() => {
    scene.classList.add('camera-push');
    card.classList.add('visible');
  }, 5600);
}

function setupLoginForm() {
  const form = document.getElementById('loginForm');
  if (!form) return;

  const errorBox = document.getElementById('loginError');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const username = (usernameInput.value || '').trim();
    const password = (passwordInput.value || '').trim();

    if (!username || !password) {
      errorBox.textContent = 'Please enter both username/email and password.';
      errorBox.style.display = 'block';
      return;
    }

    errorBox.style.display = 'none';

    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Login failed.');
      }

      window.location.href = data.redirect || '/chatbot';
    } catch (error) {
      errorBox.textContent = error.message || 'Something went wrong during login.';
      errorBox.style.display = 'block';
    }
  });
}

function setupRegisterForm() {
  const form = document.getElementById('registerForm');
  if (!form) return;

  const errorBox = document.getElementById('registerError');
  const successBox = document.getElementById('registerSuccess');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const payload = {
      name: document.getElementById('reg-name').value.trim(),
      email: document.getElementById('reg-email').value.trim(),
      username: document.getElementById('reg-username').value.trim(),
      password: document.getElementById('reg-password').value,
      confirm_password: document.getElementById('reg-confirm-password').value,
    };

    if (!payload.name || !payload.email || !payload.username || !payload.password || !payload.confirm_password) {
      errorBox.textContent = 'All fields are required.';
      successBox.style.display = 'none';
      errorBox.style.display = 'block';
      return;
    }

    errorBox.style.display = 'none';
    successBox.style.display = 'none';

    try {
      const response = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Registration failed.');
      }

      successBox.textContent = data.message || 'Registration successful.';
      successBox.style.display = 'block';
      form.reset();

      setTimeout(() => {
        window.location.href = '/login';
      }, 1200);
    } catch (error) {
      errorBox.textContent = error.message || 'Something went wrong during registration.';
      errorBox.style.display = 'block';
    }
  });
}

function setupChatInterface() {
  const chatForm = document.getElementById('chatForm');
  if (!chatForm) return;

  const citySelect = document.getElementById('citySelect');
  const chatInput = document.getElementById('chatInput');
  const clearChatBtn = document.getElementById('clearChatBtn');
  const typingIndicator = document.getElementById('typingIndicator');
  const chatMessages = document.getElementById('chatMessages');

  function appendMessage(role, text) {
    const row = document.createElement('div');
    row.className = `message-row ${role === 'user' ? 'user' : ''}`;

    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${role === 'user' ? 'user-bubble' : 'bot-bubble'}`;
    bubble.textContent = text;

    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showTyping(show) {
    typingIndicator.classList.toggle('hidden', !show);
  }

  async function loadChatHistory() {
    try {
      const response = await fetch('/api/chat/history');
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Unable to load chat history');
      }

      chatMessages.innerHTML = '';

      if (!data.history || data.history.length === 0) {
        appendMessage('bot', 'Hello! Choose your city and ask me about tourist spots, food, hospitals, transport, weather, or local events.');
        return;
      }

      data.history.forEach((item) => {
        appendMessage('user', item.message);
        appendMessage('bot', item.response);
      });
    } catch (error) {
      appendMessage('bot', 'There was a problem loading your previous chat history.');
    }
  }

  const promptButtons = document.querySelectorAll('.prompt-chip');
  promptButtons.forEach((button) => {
    button.addEventListener('click', () => {
      chatInput.value = button.textContent.trim();
      chatInput.focus();
    });
  });

  chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const city = citySelect ? citySelect.value : 'New York';
    const message = (chatInput.value || '').trim();

    if (!message) return;

    appendMessage('user', message);
    chatInput.value = '';
    showTyping(true);

    const tempBotReply = document.createElement('div');
    tempBotReply.className = 'message-row';
    const tempBubble = document.createElement('div');
    tempBubble.className = 'message-bubble bot-bubble';
    tempBubble.textContent = 'Thinking...';
    tempBotReply.appendChild(tempBubble);
    chatMessages.appendChild(tempBotReply);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city, message }),
      });

      const data = await response.json();
      tempBubble.textContent = data.response || 'I can help you with city information.';
      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Unable to get a response');
      }
    } catch (error) {
      tempBubble.textContent = error.message || 'Sorry, I could not answer that question right now.';
    } finally {
      showTyping(false);
    }
  });

  clearChatBtn?.addEventListener('click', async () => {
    try {
      const response = await fetch('/api/chat/history', { method: 'DELETE' });
      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Could not clear history');
      }
      chatMessages.innerHTML = '';
      appendMessage('bot', 'Chat history cleared. Ask me about your city!');
    } catch (error) {
      appendMessage('bot', error.message || 'Unable to clear the chat history.');
    }
  });

  chatInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      chatForm.requestSubmit();
    }
  });

  loadChatHistory();
}

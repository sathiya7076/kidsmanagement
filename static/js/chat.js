// Virtual Daycare Platform - Real-time & AJAX Chat Handler

document.addEventListener('DOMContentLoaded', function () {
  const chatContainer = document.getElementById('chatContainer');
  if (!chatContainer) return;

  const childId = chatContainer.dataset.childId;
  const currentUserId = parseInt(chatContainer.dataset.userId);
  const chatMessages = document.getElementById('chatMessages');
  const chatForm = document.getElementById('chatForm');
  const messageInput = document.getElementById('messageContentInput');
  const alertCheck = document.getElementById('isAlertCheck');
  const alertSeverityGroup = document.getElementById('alertSeverityGroup');
  const alertSeveritySelect = document.getElementById('alertSeveritySelect');

  // Toggle emergency alert severity selector
  if (alertCheck && alertSeverityGroup) {
    alertCheck.addEventListener('change', function () {
      if (this.checked) {
        alertSeverityGroup.classList.remove('d-none');
      } else {
        alertSeverityGroup.classList.add('d-none');
      }
    });
  }

  // Auto-scroll to bottom
  scrollToBottom();

  // SocketIO setup
  let socket = null;
  if (typeof io !== 'undefined') {
    try {
      socket = io();
      socket.on('connect', function () {
        socket.emit('join_child_chat', { child_id: childId });
      });

      socket.on('new_chat_message', function (msg) {
        // Only append if it's from another user (to avoid duplicate from our own immediate send)
        if (msg.sender_id !== currentUserId) {
          appendMessage(msg, false);
          scrollToBottom();
        }
      });
    } catch (e) {
      console.warn('SocketIO connection fallback to AJAX polling:', e);
    }
  }

  // Chat form submit
  if (chatForm) {
    chatForm.addEventListener('submit', function (e) {
      e.preventDefault();

      const content = messageInput.value.trim();
      const isAlert = alertCheck ? alertCheck.checked : false;
      const severity = alertSeveritySelect ? alertSeveritySelect.value : 'info';

      if (!content) return;

      // Disable button briefly
      const submitBtn = chatForm.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.disabled = true;

      // Send via AJAX API
      fetch(`/api/messages/${childId}/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content: content,
          is_alert: isAlert,
          alert_severity: severity
        })
      })
        .then(res => res.json())
        .then(data => {
          if (data.success && data.message) {
            appendMessage(data.message, true);
            messageInput.value = '';
            if (alertCheck) {
              alertCheck.checked = false;
              if (alertSeverityGroup) alertSeverityGroup.classList.add('d-none');
            }
            scrollToBottom();
          } else {
            alert(data.error || 'Failed to send message');
          }
        })
        .catch(err => {
          console.error('Error sending message:', err);
        })
        .finally(() => {
          if (submitBtn) submitBtn.disabled = false;
          messageInput.focus();
        });
    });
  }

  // Backup polling every 5 seconds to ensure sync
  let lastKnownMsgId = 0;
  const existingMessages = document.querySelectorAll('.message-bubble[data-msg-id]');
  if (existingMessages.length > 0) {
    lastKnownMsgId = parseInt(existingMessages[existingMessages.length - 1].dataset.msgId);
  }

  setInterval(function () {
    fetch(`/api/messages/${childId}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.messages) {
          data.messages.forEach(msg => {
            if (msg.id > lastKnownMsgId) {
              lastKnownMsgId = msg.id;
              if (msg.sender_id !== currentUserId) {
                appendMessage(msg, false);
                scrollToBottom();
              }
            }
          });
        }
      })
      .catch(e => console.warn('Polling error:', e));
  }, 5000);

  function appendMessage(msg, isOutgoing) {
    if (!chatMessages) return;

    // Remove empty state placeholder if present
    const emptyState = document.getElementById('chatEmptyState');
    if (emptyState) emptyState.remove();

    const bubble = document.createElement('div');
    const outgoingClass = isOutgoing ? 'message-outgoing' : 'message-incoming';
    const alertClass = msg.is_alert ? 'message-alert' : '';

    bubble.className = `message-bubble ${outgoingClass} ${alertClass}`;
    bubble.dataset.msgId = msg.id;

    let alertHeader = '';
    if (msg.is_alert) {
      alertHeader = `
        <div class="fw-bold text-danger mb-1 small">
          <i class="bi bi-exclamation-triangle-fill me-1"></i> PRIORITY ALERT
        </div>
      `;
    }

    bubble.innerHTML = `
      ${alertHeader}
      <div class="message-content">${escapeHtml(msg.content)}</div>
      <span class="message-time ${isOutgoing ? 'text-white-50' : 'text-muted'}">
        ${escapeHtml(msg.sender_name || '')} • ${escapeHtml(msg.timestamp || 'Just now')}
      </span>
    `;

    chatMessages.appendChild(bubble);
  }

  function scrollToBottom() {
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
});

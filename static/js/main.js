// Virtual Daycare Platform - Main Client Script

document.addEventListener('DOMContentLoaded', function () {
  initNotifications();
  initDatepickerAutoSubmit();
});

// SocketIO reference
let globalSocket = null;
if (typeof io !== 'undefined') {
  try {
    globalSocket = io();
    globalSocket.on('connect', function () {
      globalSocket.emit('join_user_notifications', {});
    });

    globalSocket.on('new_notification', function (notif) {
      updateBellBadge(1, true); // increment badge count
      showToastNotification(notif.title, notif.message, notif.is_urgent);
    });
  } catch (e) {
    console.log('SocketIO initialization fallback to polling:', e);
  }
}

function initNotifications() {
  const bellBtn = document.getElementById('notificationBellBtn');
  const notifDropdown = document.getElementById('notificationListContainer');
  const markAllBtn = document.getElementById('markAllReadBtn');

  if (!bellBtn) return;

  // Initial fetch of unread count
  fetchNotifications();

  // Periodic polling every 15 seconds as a reliable backup
  setInterval(fetchNotifications, 15000);

  if (markAllBtn) {
    markAllBtn.addEventListener('click', function (e) {
      e.preventDefault();
      fetch('/api/notifications/mark-all-read', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            updateBellBadge(0, false);
            fetchNotifications();
          }
        });
    });
  }
}

function fetchNotifications() {
  fetch('/api/notifications/unread')
    .then(res => res.json())
    .then(data => {
      updateBellBadge(data.count, false);
      renderNotificationDropdown(data.notifications, data.count);
    })
    .catch(err => console.error('Error fetching notifications:', err));
}

function updateBellBadge(count, isIncrement) {
  const badge = document.getElementById('notificationBadge');
  if (!badge) return;

  let current = parseInt(badge.textContent || '0');
  let finalCount = isIncrement ? current + count : count;

  if (finalCount > 0) {
    badge.textContent = finalCount > 9 ? '9+' : finalCount;
    badge.classList.remove('d-none');
  } else {
    badge.textContent = '0';
    badge.classList.add('d-none');
  }
}

function renderNotificationDropdown(notifications, totalCount) {
  const container = document.getElementById('notificationListContainer');
  if (!container) return;

  if (!notifications || notifications.length === 0) {
    container.innerHTML = `
      <div class="text-center py-4 text-muted">
        <i class="bi bi-bell-slash fs-3 d-block mb-1"></i>
        <small>No unread notifications</small>
      </div>
    `;
    return;
  }

  let html = '';
  notifications.forEach(n => {
    const urgentClass = n.is_urgent ? 'border-start border-danger border-4 bg-danger-subtle' : '';
    const urgentBadge = n.is_urgent ? '<span class="badge bg-danger ms-1">Urgent</span>' : '';
    html += `
      <div class="notification-item unread ${urgentClass}" onclick="handleNotificationClick(${n.id}, '${n.link}')">
        <div class="d-flex justify-content-between align-items-start mb-1">
          <strong class="small text-dark">${escapeHtml(n.title)} ${urgentBadge}</strong>
          <small class="text-muted" style="font-size: 0.7rem;">${n.created_at}</small>
        </div>
        <p class="mb-0 text-muted small" style="font-size: 0.8rem; line-height: 1.3;">${escapeHtml(n.message)}</p>
      </div>
    `;
  });

  container.innerHTML = html;
}

function handleNotificationClick(notifId, link) {
  fetch(`/api/notifications/mark-read/${notifId}`, { method: 'POST' })
    .finally(() => {
      if (link && link !== '#' && link !== 'null') {
        window.location.href = link;
      } else {
        fetchNotifications();
      }
    });
}

function showToastNotification(title, message, isUrgent) {
  const toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) return;

  const toastId = 'toast_' + Date.now();
  const bgClass = isUrgent ? 'text-bg-danger' : 'text-bg-primary';

  const toastHtml = `
    <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 shadow" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">
          <strong>${escapeHtml(title)}</strong>
          <div class="small mt-1">${escapeHtml(message)}</div>
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;

  toastContainer.insertAdjacentHTML('beforeend', toastHtml);
  const toastEl = document.getElementById(toastId);
  if (toastEl && typeof bootstrap !== 'undefined') {
    const bsToast = new bootstrap.Toast(toastEl, { delay: isUrgent ? 10000 : 5000 });
    bsToast.show();
  }
}

function initDatepickerAutoSubmit() {
  const dateInput = document.getElementById('timelineDatepicker');
  if (dateInput) {
    dateInput.addEventListener('change', function () {
      const selectedDate = this.value;
      const url = new URL(window.location.href);
      url.searchParams.set('date', selectedDate);
      window.location.href = url.toString();
    });
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// common.js - 公共函数库

// 获取当前登录用户信息
function getUserInfo() {
    const user_id = localStorage.getItem('user_id');
    const username = localStorage.getItem('username');
    const email = localStorage.getItem('email');

    if (!user_id || !username) {
        return null;
    }

    return {
        user_id: parseInt(user_id),
        username: username,
        email: email || '',
        login_time: localStorage.getItem('login_time')
    };
}

// 检查登录状态
function checkLogin() {
    const user = getUserInfo();
    if (!user) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// 退出登录
function logout() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('email');
    localStorage.removeItem('login_time');
    window.location.href = 'login.html';
}

// 显示消息
function showMessage(message, type = 'info', duration = 3000) {
    // 移除旧的消息框
    const oldAlert = document.querySelector('.custom-alert');
    if (oldAlert) oldAlert.remove();

    // 创建消息框
    const alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;

    const typeText = {
        'success': '成功',
        'warning': '警告',
        'error': '错误',
        'info': '提示'
    }[type] || '提示';

    alertDiv.innerHTML = `
        <strong>${typeText}:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    // 自动消失
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }
}

// API请求封装
const api = {
    get: async (url, params = {}) => {
        try {
            const query = new URLSearchParams(params).toString();
            const fullUrl = query ? `/api/${url}?${query}` : `/api/${url}`;
            const response = await axios.get(fullUrl);
            return response.data;
        } catch (error) {
            handleApiError(error);
            throw error;
        }
    },

    post: async (url, data = {}) => {
        try {
            const response = await axios.post(`/api/${url}`, data);
            return response.data;
        } catch (error) {
            handleApiError(error);
            throw error;
        }
    }
};

// 处理API错误
function handleApiError(error) {
    if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        switch (status) {
            case 401:
                showMessage('登录已过期，请重新登录', 'warning');
                setTimeout(() => logout(), 1500);
                break;
            case 403:
                showMessage('权限不足', 'error');
                break;
            case 404:
                showMessage('请求的资源不存在', 'error');
                break;
            case 500:
                showMessage('服务器内部错误', 'error');
                break;
            default:
                showMessage(data.message || '请求失败', 'error');
        }
    } else if (error.request) {
        showMessage('网络连接失败，请检查网络或服务器状态', 'error');
    } else {
        showMessage('请求错误: ' + error.message, 'error');
    }
}

// 价格格式化
function formatPrice(price) {
    return '¥' + parseFloat(price).toFixed(2);
}

// 时间格式化
function formatTime(dateString) {
    if (!dateString) return '未知时间';

    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    // 小于1分钟
    if (diff < 60000) {
        return '刚刚';
    }

    // 小于1小时
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
    }

    // 小于1天
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
    }

    // 小于30天
    if (diff < 2592000000) {
        const days = Math.floor(diff / 86400000);
        return `${days}天前`;
    }

    // 返回完整日期
    return date.toLocaleDateString('zh-CN') + ' ' +
           date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'});
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 截断文本
function truncateText(text, maxLength = 50) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// 获取URL参数
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 设置页面标题
function setPageTitle(title) {
    document.title = title + ' - 校园二手交易平台';
}

// 初始化页面
function initPage() {
    // 检查登录状态
    if (!window.location.href.includes('login.html') &&
        !window.location.href.includes('register.html')) {
        checkLogin();
    }

    // 显示用户信息
    const user = getUserInfo();
    if (user) {
        const userElements = document.querySelectorAll('.user-info');
        userElements.forEach(el => {
            el.textContent = user.username;
        });
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
} else {
    initPage();
}
// 获取用户ID（添加到 common.js 末尾）
function getUserId() {
    const user = getUserInfo();
    return user ? user.user_id : null;
}
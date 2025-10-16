// File chính xử lý logic dashboard

// Biến theo dõi hiệu suất
let sseLatency = 0;
let wsLatency = 0;
let ssePerformanceData = {};
let wsPerformanceData = {};

// Các hàm tiện ích
function log(message) {
  const logDiv = document.getElementById('activityLog');
  const time = new Date().toLocaleTimeString();
  logDiv.innerHTML += `<div>[${time}] ${message}</div>`;
  logDiv.scrollTop = logDiv.scrollHeight;
}

function updateStatus(element, status, isConnected) {
  // Xác định class dựa trên status text
  let className = 'status-item ';
  if (status.includes('Fallback') || status.includes('fallback')) {
    className += 'status-fallback';
  } else if (isConnected) {
    className += 'status-connected';
  } else {
    className += 'status-disconnected';
  }
  
  element.className = className;
  element.textContent = status;
}

// Quản lý trạng thái kết nối
function updateConnectionUI(type, connected) {
  const connectBtn = document.getElementById(`${type}ConnectBtn`);
  const disconnectBtn = document.getElementById(`${type}DisconnectBtn`);
  const connectionStatus = document.getElementById(`${type}ConnectionStatus`);
  
  if (connected) {
    connectBtn.disabled = true;
    disconnectBtn.disabled = false;
    
    // Kiểm tra fallback mode
    const isFallback = (type === 'sse' && typeof sseFallbackMode !== 'undefined' && sseFallbackMode) ||
                      (type === 'ws' && typeof wsFallbackMode !== 'undefined' && wsFallbackMode);
    
    if (isFallback) {
      connectionStatus.textContent = 'Fallback Mode';
      connectionStatus.className = 'connection-status status-fallback';
    } else {
      connectionStatus.textContent = 'Đã kết nối';
      connectionStatus.className = 'connection-status status-connected';
    }
  } else {
    connectBtn.disabled = false;
    disconnectBtn.disabled = true;
    connectionStatus.textContent = 'Chưa kết nối';
    connectionStatus.className = 'connection-status status-disconnected';
  }
}

// So sánh hiệu suất
function updateComparison() {
  // So sánh mức sử dụng CPU
  if (ssePerformanceData.cpu_usage !== undefined && wsPerformanceData.cpu_usage !== undefined) {
    document.getElementById('sseCpuUsage').textContent = ssePerformanceData.cpu_usage + '%';
    document.getElementById('wsCpuUsage').textContent = wsPerformanceData.cpu_usage + '%';
    document.getElementById('cpuWinner').textContent = 
      ssePerformanceData.cpu_usage < wsPerformanceData.cpu_usage ? 'SSE' : 'WebSocket';
  }

  // So sánh mức sử dụng bộ nhớ
  if (ssePerformanceData.memory_usage !== undefined && wsPerformanceData.memory_usage !== undefined) {
    document.getElementById('sseMemoryUsage').textContent = ssePerformanceData.memory_usage + '%';
    document.getElementById('wsMemoryUsage').textContent = wsPerformanceData.memory_usage + '%';
    document.getElementById('memoryWinner').textContent = 
      ssePerformanceData.memory_usage < wsPerformanceData.memory_usage ? 'SSE' : 'WebSocket';
  }

  // So sánh thông lượng
  if (ssePerformanceData.throughput !== undefined && wsPerformanceData.throughput !== undefined) {
    document.getElementById('sseThroughputComp').textContent = ssePerformanceData.throughput;
    document.getElementById('wsThroughputComp').textContent = wsPerformanceData.throughput;
    document.getElementById('throughputWinner').textContent = 
      ssePerformanceData.throughput > wsPerformanceData.throughput ? 'SSE' : 'WebSocket';
  }
}

// Kiểm tra độ trễ
function testLatency() {
  log('Đang kiểm tra độ trễ...');
  
  // Kiểm tra độ trễ WebSocket với ping-pong
  if (ws && ws.connected) {
    ws.emit("ping", { timestamp: Date.now() / 1000 });
  }
  
  // Độ trễ SSE được đo tự động từ send_time
  setTimeout(() => {
    log(`Kiểm tra độ trễ hoàn tất - SSE: ${sseLatency}ms, WebSocket: ${wsLatency}ms`);
  }, 100);
}

// Xóa nhật ký
function clearLogs() {
  document.getElementById('activityLog').innerHTML = '<div>Đã xóa nhật ký...</div>';
}

// Khởi tạo dashboard
function initializeDashboard() {
  log('Dashboard đã được khởi tạo. Sử dụng nút Kết nối để bắt đầu.');
  updateConnectionUI('sse', false);
  updateConnectionUI('ws', false);

  // Tự động làm mới thống kê mỗi 5 giây
  setInterval(() => {
    if (ws && ws.connected) {
      ws.emit("get_stats");
    }
  }, 5000);
}

// Khởi tạo khi DOM đã tải xong
document.addEventListener('DOMContentLoaded', initializeDashboard);

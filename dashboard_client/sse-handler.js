// Xử lý Server-Sent Events (SSE)

let sseConnected = false;
let sseSource = null;
let ssePerformanceSource = null;
let sseFallbackMode = false;
let sseFallbackInterval = null;
let sseReconnectAttempts = 0;
let ssePollingCount = 0; // Counter cho polling để thử reconnect
let sseMaxReconnectAttempts = 100;
let sseManuallyStarted = false; // Biến để tracking xem có được start thủ công không

const sseStatus = document.getElementById('sseStatus');

// Kết nối SSE
function connectSSE(isAutoReconnect = false) {
  if (sseConnected && !sseFallbackMode) {
    log('SSE đã được kết nối');
    return;
  }

  // Nếu không phải auto-reconnect thì đánh dấu là manually started
  if (!isAutoReconnect) {
    sseManuallyStarted = true;
  }

  // Kiểm tra xem EventSource có được hỗ trợ không
  if (typeof EventSource === 'undefined') {
    log('Lỗi: Trình duyệt không hỗ trợ EventSource (SSE) - chuyển sang fallback mode');
    startSSEFallback();
    return;
  }

  try {
    log('Đang kết nối SSE...');
    sseSource = new EventSource("https://websocket-c88q.onrender.com/stream");
    
    sseSource.onopen = () => {
      sseConnected = true;
      sseFallbackMode = false;
      sseReconnectAttempts = 0;
      ssePollingCount = 0; // Reset polling count
      
      // Clear fallback interval nếu có
      if (sseFallbackInterval) {
        clearInterval(sseFallbackInterval);
        sseFallbackInterval = null;
      }
      
      updateStatus(sseStatus, 'SSE: Đã kết nối ✅', true);
      updateConnectionUI('sse', true);
      log('SSE kết nối thành công');
    };

    sseSource.onmessage = event => {
      const data = JSON.parse(event.data);
      document.getElementById("sseValue").textContent = data.value;
      document.getElementById("sseTime").textContent = "Cập nhật lúc " + data.timestamp;
      
      // Tính độ trễ cho SSE
      if (data.send_time) {
        sseLatency = Math.round((Date.now() / 1000 - data.send_time) * 1000);
        document.getElementById("sseLatency").textContent = sseLatency + " ms";
      }
    };

    sseSource.onerror = (error) => {
      log('SSE mất kết nối - chuyển sang fallback mode...');
      
      // Chỉ chuyển sang fallback nếu đã được manually started
      if (sseManuallyStarted && !sseFallbackMode) {
        startSSEFallback();
      }
    };

    // Kết nối luồng dữ liệu hiệu suất
    connectSSEPerformance();

  } catch (error) {
    log('SSE kết nối thất bại: ' + error.message + ' - chuyển sang fallback mode');
    startSSEFallback();
  }
}

function connectSSEPerformance() {
  try {
    ssePerformanceSource = new EventSource("https://websocket-c88q.onrender.com/performance");
    ssePerformanceSource.onmessage = event => {
      const data = JSON.parse(event.data);
      ssePerformanceData = data;
      
      document.getElementById("sseConnections").textContent = data.connections;
      document.getElementById("sseMessages").textContent = data.messages_sent;
      document.getElementById("sseThroughput").textContent = data.throughput;
      document.getElementById("sseUptime").textContent = data.uptime;
      
      updateComparison();
    };

    ssePerformanceSource.onerror = (error) => {
      log('Lỗi kết nối luồng hiệu suất SSE - sử dụng fallback performance');
      // startSSEPerformanceFallback(); // Comment out
    };
  } catch (error) {
    // startSSEPerformanceFallback(); // Comment out
  }
}

// SSE Fallback functions
function startSSEFallback() {
  // Chỉ start fallback nếu đã được manually started trước đó
  if (!sseManuallyStarted) {
    log('SSE: Chưa được kết nối thủ công, không start fallback');
    return;
  }

  if (sseFallbackMode) {
    return; // Đã trong fallback mode
  }

  log('Khởi động SSE fallback mode (HTTP polling)...');
  sseFallbackMode = true;
  sseConnected = false; // Set false vì không phải real connection
  
  updateStatus(sseStatus, 'SSE: Fallback mode 🔄', true);
  updateConnectionUI('sse', true);
  
  // Polling data từ fallback endpoint
  sseFallbackInterval = setInterval(() => {
    fetch('https://websocket-c88q.onrender.com/fallback/polling')
      .then(response => response.json())
      .then(data => {
        if (data.messages && data.messages.length > 0) {
          const latestMessage = data.messages[data.messages.length - 1];
          document.getElementById("sseValue").textContent = latestMessage.value;
          document.getElementById("sseTime").textContent = "Fallback: " + latestMessage.timestamp;
          
          if (latestMessage.send_time) {
            sseLatency = Math.round((Date.now() / 1000 - latestMessage.send_time) * 1000) + 200;
            document.getElementById("sseLatency").textContent = sseLatency + " ms (fallback)";
          }
        }
        
        // Thử kết nối lại EventSource mỗi 10 giây
        ssePollingCount++;
        if (ssePollingCount % 5 === 0) { // 5 * 2s = 10s
          tryReconnectSSE();
        }
      })
      .catch(error => {
        log('SSE fallback polling lỗi: ' + error.message);
      });
  }, 2000);
  
  // startSSEPerformanceFallback(); // Comment out vì function không tồn tại
}

function tryReconnectSSE() {
  if (!sseFallbackMode) return;
  
  log('SSE: Thử kết nối lại EventSource...');
  
  // Tạo EventSource mới để test
  try {
    const testSource = new EventSource("https://websocket-c88q.onrender.com/stream");
    
    const timeout = setTimeout(() => {
      testSource.close();
      log('SSE: Test connection timeout');
    }, 3000);
    
    testSource.onopen = () => {
      clearTimeout(timeout);
      testSource.close();
      
      log('SSE: Server đã khôi phục, chuyển về connection mode');
      
      // Cleanup fallback
      clearInterval(sseFallbackInterval);
      sseFallbackInterval = null;
      sseFallbackMode = false;
      ssePollingCount = 0;
      
      // Tạo connection thật
      connectSSE(true);
    };
    
    testSource.onerror = () => {
      clearTimeout(timeout);
      testSource.close();
    };
    
  } catch (error) {
    log('SSE: Lỗi khi test reconnect: ' + error.message);
  }
}

// Ngắt kết nối SSE
function disconnectSSE() {
  if (!sseConnected && !sseFallbackMode) {
    log('SSE đã ngắt kết nối');
    return;
  }

  try {
    // Đóng EventSource nếu có
    if (sseSource) {
      sseSource.close();
      sseSource = null;
    }
    if (ssePerformanceSource) {
      ssePerformanceSource.close();
      ssePerformanceSource = null;
    }
    
    // Đóng fallback polling nếu có
    if (sseFallbackInterval) {
      clearInterval(sseFallbackInterval);
      sseFallbackInterval = null;
    }
    
    sseConnected = false;
    sseFallbackMode = false;
    sseReconnectAttempts = 0;
    sseManuallyStarted = false; // Reset flag khi disconnect thủ công
    updateStatus(sseStatus, 'SSE: Đã ngắt kết nối ⏸️', false);
    updateConnectionUI('sse', false);
    
    // Xóa hiển thị dữ liệu
    document.getElementById("sseValue").textContent = '--';
    document.getElementById("sseTime").textContent = 'Đã ngắt kết nối';
    
    log('SSE đã ngắt kết nối thủ công');
  } catch (error) {
    log('Lỗi khi ngắt kết nối SSE: ' + error.message);
  }
}

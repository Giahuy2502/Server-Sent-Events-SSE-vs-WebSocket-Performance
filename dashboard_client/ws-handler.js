// Xử lý WebSocket - Phiên bản đơn giản

let wsConnected = false;
let ws = null;
let wsFallbackMode = false;
let wsFallbackInterval = null;
let wsReconnectInterval = null;
let wsManuallyStarted = false;

const wsStatus = document.getElementById('wsStatus');

// Kết nối WebSocket
function connectWebSocket(isAutoReconnect = false) {
  if (wsConnected && !wsFallbackMode) {
    log('WebSocket đã được kết nối');
    return;
  }

  if (!isAutoReconnect) {
    wsManuallyStarted = true;
  }

  if (typeof io === 'undefined') {
    log('Lỗi: socket.io client chưa được tải');
    startWebSocketFallback();
    return;
  }

  try {
    log('Đang kết nối WebSocket...');
    
    if (ws) {
      ws.disconnect();
    }
    
    ws = io("https://websocket-jaoq.onrender.com");

    ws.on("connect", () => {
      wsConnected = true;
      wsFallbackMode = false;
      
      // Clear fallback
      if (wsFallbackInterval) {
        clearInterval(wsFallbackInterval);
        wsFallbackInterval = null;
      }
      if (wsReconnectInterval) {
        clearInterval(wsReconnectInterval);
        wsReconnectInterval = null;
      }
      
      updateStatus(wsStatus, 'WebSocket: Đã kết nối ✅', true);
      updateConnectionUI('ws', true);
      log('WebSocket kết nối thành công');
    });

    ws.on("connect_error", (err) => {
      log('WebSocket lỗi kết nối: ' + err);
      if (wsManuallyStarted && !wsFallbackMode) {
        startWebSocketFallback();
        startAutoReconnect();
      }
    });

    ws.on("disconnect", (reason) => {
      wsConnected = false;
      log('WebSocket ngắt kết nối: ' + reason);
      
      if (reason !== 'io client disconnect' && wsManuallyStarted && !wsFallbackMode) {
        startWebSocketFallback();
        startAutoReconnect();
      }
    });

    ws.on("update", (data) => {
      document.getElementById("wsValue").textContent = data.value;
      document.getElementById("wsTime").textContent = "Cập nhật lúc " + data.timestamp;
      
      if (data.send_time) {
        wsLatency = Math.round((Date.now() / 1000 - data.send_time) * 1000);
        document.getElementById("wsLatency").textContent = wsLatency + " ms";
      }
    });

    ws.on("performance", (data) => {
      wsPerformanceData = data;
      document.getElementById("wsConnections").textContent = data.connections;
      document.getElementById("wsMessages").textContent = data.messages_sent;
      document.getElementById("wsThroughput").textContent = data.throughput;
      document.getElementById("wsUptime").textContent = data.uptime;
      updateComparison();
    });

  } catch (error) {
    log('WebSocket kết nối thất bại: ' + error.message);
    if (wsManuallyStarted) {
      startWebSocketFallback();
      startAutoReconnect();
    }
  }
}

// Fallback mode đơn giản
function startWebSocketFallback() {
  if (!wsManuallyStarted || wsFallbackMode) {
    return;
  }

  log('Khởi động WebSocket fallback mode...');
  wsFallbackMode = true;
  wsConnected = false;
  
  updateStatus(wsStatus, 'WebSocket: Fallback mode 🔄', true);
  updateConnectionUI('ws', true);
  
  wsFallbackInterval = setInterval(() => {
    fetch('https://websocket-jaoq.onrender.com/fallback/polling')
      .then(response => response.json())
      .then(data => {
        if (data.messages && data.messages.length > 0) {
          const latestMessage = data.messages[data.messages.length - 1];
          document.getElementById("wsValue").textContent = latestMessage.value;
          document.getElementById("wsTime").textContent = "Fallback: " + latestMessage.timestamp;
          
          if (latestMessage.send_time) {
            wsLatency = Math.round((Date.now() / 1000 - latestMessage.send_time) * 1000) + 300;
            document.getElementById("wsLatency").textContent = wsLatency + " ms (fallback)";
          }
        }
      })
      .catch(error => {
        log('WebSocket fallback lỗi: ' + error.message);
      });
  }, 2500);
  
  startWebSocketPerformanceFallback();
}

// Auto-reconnect đơn giản
function startAutoReconnect() {
  if (wsReconnectInterval) {
    return;
  }
  
  log('Khởi động auto-reconnect mỗi 5 giây...');
  
  wsReconnectInterval = setInterval(() => {
    if (wsFallbackMode) {
      log('Thử kết nối lại WebSocket...');
      
      // Clear fallback tạm thời
      if (wsFallbackInterval) {
        clearInterval(wsFallbackInterval);
        wsFallbackInterval = null;
      }
      
      wsFallbackMode = false;
      connectWebSocket(true);
    }
  }, 5000);
}

// Performance fallback
function startWebSocketPerformanceFallback() {
  setInterval(() => {
    if (wsFallbackMode) {
      fetch('https://websocket-jaoq.onrender.com/fallback/performance')
        .then(response => response.json())
        .then(data => {
          wsPerformanceData = data;
          document.getElementById("wsConnections").textContent = data.connections;
          document.getElementById("wsMessages").textContent = data.messages_sent;
          document.getElementById("wsThroughput").textContent = data.throughput;
          document.getElementById("wsUptime").textContent = data.uptime;
          updateComparison();
        })
        .catch(error => {
          // Ignore errors
        });
    }
  }, 5000);
}

// Ngắt kết nối
function disconnectWebSocket() {
  if (!wsConnected && !wsFallbackMode) {
    return;
  }

  try {
    if (ws && ws.connected) {
      ws.disconnect();
    }
    
    if (wsFallbackInterval) {
      clearInterval(wsFallbackInterval);
      wsFallbackInterval = null;
    }
    if (wsReconnectInterval) {
      clearInterval(wsReconnectInterval);
      wsReconnectInterval = null;
    }
    
    wsConnected = false;
    wsFallbackMode = false;
    wsManuallyStarted = false;
    
    updateStatus(wsStatus, 'WebSocket: Đã ngắt kết nối ⏸️', false);
    updateConnectionUI('ws', false);
    
    document.getElementById("wsValue").textContent = '--';
    document.getElementById("wsTime").textContent = 'Đã ngắt kết nối';
    
    log('WebSocket đã ngắt kết nối');
  } catch (error) {
    log('Lỗi khi ngắt kết nối WebSocket: ' + error.message);
  }
}
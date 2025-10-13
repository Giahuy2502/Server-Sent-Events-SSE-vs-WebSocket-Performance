# 🚀 SSE vs WebSocket Performance Demo

## 📝 Mô tả
Demo này giúp bạn so sánh hiệu suất giữa **Server-Sent Events (SSE)** và **WebSocket** thông qua một giao diện web đơn giản.

## 🎯 Mục đích
- So sánh tốc độ truyền dữ liệu
- Đo độ trễ (latency) 
- Theo dõi mức sử dụng CPU và RAM
- Hiểu rõ ưu nhược điểm của từng phương pháp

## Mục so sánh

### 1. Dữ liệu thời gian thực
- **SSE**: Số màu xanh dương - cập nhật mỗi giây
- **WebSocket**: Số màu xanh lá - cập nhật mỗi giây

### 2. Bảng so sánh hiệu suất
| Tiêu chí | SSE | WebSocket | Ai thắng? |
|----------|-----|-----------|-----------|
| **CPU Usage** | Thường thấp hơn | Thường cao hơn | SSE |
| **Memory Usage** | Ít hơn | Nhiều hơn | SSE |
| **Throughput** | Ổn định | Có thể cao hơn | Tuỳ thuộc |
| **Latency** | One-way | Round-trip | WebSocket |

### 3. Các số liệu quan trọng
- **Connections**: Số người đang kết nối
- **Messages**: Tổng tin nhắn đã gửi
- **Throughput**: Tin nhắn/giây
- **Uptime**: Thời gian hoạt động

## 🔍 So sánh SSE vs WebSocket

### Server-Sent Events (SSE)
✅ **Ưu điểm:**
- Đơn giản, dễ hiểu
- Tự động kết nối lại khi mất mạng
- Ít tốn tài nguyên máy chủ
- Phù hợp với HTTP cache

❌ **Nhược điểm:**
- Chỉ gửi được từ server → client
- Giới hạn số kết nối đồng thời

🎯 **Dùng khi nào:** Thông báo, tin tức, cập nhật trạng thái

### WebSocket
✅ **Ưu điểm:**
- Gửi nhận 2 chiều (client ↔ server)
- Độ trễ thấp
- Hỗ trợ nhiều loại dữ liệu
- Không giới hạn kết nối

❌ **Nhược điểm:**
- Phức tạp hơn
- Tốn nhiều tài nguyên hơn
- Phải tự xử lý kết nối lại

🎯 **Dùng khi nào:** Chat, game online, cộng tác real-time

## 🎓 Kết luận
- **SSE**: Tốt cho ứng dụng đơn giản, ít tài nguyên
- **WebSocket**: Tốt cho ứng dụng phức tạp, cần tương tác 2 chiều
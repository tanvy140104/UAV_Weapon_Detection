# Kiểm thử backend

Dùng `python -u run_backend_tests.py`; thêm `--browser` để chạy nghiệm thu Web với Edge. Runner tạo PostgreSQL tạm riêng, sử dụng schema thật và các service/API thật. AI và phần cứng camera được thay bằng dữ liệu xác định trong những bài test cần điều khiển đầu vào.

## Ma trận yêu cầu — kiểm thử

| Yêu cầu | Bằng chứng kiểm thử |
| --- | --- |
| Backend/Web/API hoạt động | Health, readiness, Web và OpenAPI trả 200, có request ID |
| Tạo phiên có validation | Từ chối RTSP, camera sai, chuỗi rỗng, đường dẫn ngoài data/videos, trường lạ; không tạo bản ghi |
| Quản lý vòng đời | STOPPED → RUNNING → STOPPED, từ chối chuyển sai trạng thái, 404 phiên không tồn tại |
| Không chạy nguồn lỗi | Video thiếu không chuyển phiên sang RUNNING |
| Liệt kê phiên | Limit/offset và giới hạn tham số |
| Khóa khi cập nhật đồng thời | Hai luồng start có một thành công; bốn luồng ghi cùng sự kiện chỉ lưu một |
| Toàn vẹn phát hiện | Từ chối nhãn sai, NaN, bbox sai; không ghi sau khi stop |
| Lịch sử + ảnh + duyệt cảnh báo | Ghi PostgreSQL, đọc lại JPEG, CONFIRMED/FALSE_POSITIVE/NEW |
| Hoàn tác khi lỗi filesystem | Lưu ảnh thứ hai lỗi: rollback cả batch, dọn ảnh đầu |
| Hoàn tác khi lỗi PostgreSQL | Trigger test gây lỗi sau khi tạo JPEG: DB rollback, ảnh được dọn |
| Tra cứu | Lọc theo phiên/nhãn/thời gian, phân trang, tham số không chèn được SQL |
| Bảo vệ ảnh bằng chứng | 404 ảnh thiếu, 422 ID sai, 400 đường dẫn vượt thư mục evidence |
| Quản lý lỗi | DB lỗi trả 503, không lộ thông tin driver; readiness phản ánh lỗi |
| Giám sát | Lưu frame/bằng chứng, đóng capture và dừng phiên khi ngắt |
| Khôi phục phiên | AI lỗi → ERROR → STOPPED → RUNNING |
| Quyền sở hữu stream | Từ chối mở trùng; token cũ không giải phóng token hiện tại; camera chỉ có một monitor |
| Lỗi trước khi mở stream | Trả lỗi, giải phóng reservation, ghi ERROR |
| Khởi tạo DB | Chạy lặp lại không mất dữ liệu |
| API ảnh | 200 với ảnh hợp lệ, 400 ảnh rỗng/hỏng, 413 quá dung lượng, 415 sai loại, 503 AI lỗi |
| Nghiệm thu Web tùy chọn | Tạo phiên → mở giám sát → xuất hiện lịch sử → dừng → lọc → xem JPEG → xác nhận → lọc CONFIRMED; không có exception JavaScript |

## Đọc kết quả

Mỗi lần chạy lưu `results.txt`, `postgres.log` và log khởi động trong `runtime/test-runs/<run>/`. Khi chạy `--browser` có thêm `browser.log`; nếu chờ giao diện thất bại có `browser-page.txt`.

Các log exception khi cố ý gây lỗi AI/DB là đầu vào của bài test; kết luận dựa trên kết quả `OK` hoặc `FAILED` ở cuối báo cáo.

Các test mới nằm trong `tests/`. Những script trong `project_archive/tests` là thử nghiệm cũ, có thể dùng SQLite hoặc mở webcam và không nằm trong bộ test tự động hiện tại.

## Phần cần kiểm tra trên môi trường demo

- Cập nhật schema của database đang dùng qua `python -m backend.database.init_pg`.
- Chạy launcher bằng tài khoản PostgreSQL thực tế.
- Thử webcam thật, cấp quyền camera và xác nhận chất lượng ảnh.
- Dùng model thật để minh họa tích hợp AI. Test backend không chứng minh độ chính xác nhận diện.

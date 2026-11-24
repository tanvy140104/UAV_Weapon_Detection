# Demo backend — UAV Weapon Detection

## Mục tiêu trình bày

Đồ án Công nghệ phần mềm tập trung vào thiết kế backend, quản lý phiên, lưu dữ liệu, xử lý lỗi, tính toàn vẹn và kiểm thử. Webcam/video mô phỏng camera UAV; YOLO11n là thành phần AI được tích hợp.

## Chuẩn bị

Thực hiện cấu hình theo [README](README.md). Với database cũ, chạy cập nhật schema trước:

```powershell
.\.venv\Scripts\python.exe -m backend.database.init_pg
.\.venv\Scripts\python.exe run_backend_pg.py
```

Web: http://127.0.0.1:8003/web/  
Swagger: http://127.0.0.1:8003/docs

Kiểm tra `GET /health/ready` trả 200. Mật khẩu lấy từ biến môi trường/`.env` hoặc nhập ẩn khi chạy.

## Kịch bản 1 — Quản lý phiên và nguồn video

1. Nhập `data/videos/test.mp4`, tạo phiên.
2. Chỉ ra session ID, trạng thái STOPPED và nguồn trong `GET /sessions/{id}`.
3. Bắt đầu giám sát, kiểm tra RUNNING và video trên Web.
4. Dừng, kiểm tra STOPPED; thử gọi stop lần nữa trên Swagger để minh họa 409.
5. Tạo nguồn `data/videos/absent.mp4`, gọi start: nhận 404 và phiên giữ STOPPED.
6. Gửi đường dẫn ngoài `data/videos` hoặc RTSP: nhận 422, không tạo phiên.

Video `test.mp4` hiện là hình mô phỏng chuyển động để kiểm tra truyền hình, không phải bộ video kiểm chứng nhận diện vũ khí.

## Kịch bản 2 — Nhận diện, lưu lịch sử và bằng chứng

1. Nhập `0` để tạo phiên webcam, bắt đầu giám sát.
2. Dùng mẫu minh họa phù hợp để model có thể phát hiện; kết quả AI có thể chưa ổn định.
3. Khi phát hiện, chỉ ra bounding box, confidence, thời gian và session ID trong lịch sử.
4. Xem ảnh bằng chứng. Đối chiếu đường dẫn ảnh và bản ghi PostgreSQL.
5. Giữ cùng đối tượng trong vài giây để trình bày cơ chế chống lưu trùng cùng nhãn/cùng phiên trong 5 giây.
6. Dừng phiên; dữ liệu lịch sử và bằng chứng vẫn được giữ.

Không phụ thuộc hoàn toàn vào khả năng nhận diện trong buổi bảo vệ: chạy bộ kiểm thử nghiệm thu ở kịch bản 5 để chứng minh luồng backend với đầu vào xác định.

## Kịch bản 3 — Tra cứu và duyệt cảnh báo

1. Lọc theo mã phiên, loại đối tượng, trạng thái và thời gian.
2. Dùng phân trang khi có nhiều bản ghi.
3. Xem ảnh, nhấn Xác nhận hoặc Nhận diện sai.
4. Lọc CONFIRMED/FALSE_POSITIVE; đọc lại API để chứng minh trạng thái được lưu vào PostgreSQL.
5. Đặt lại cảnh báo về NEW nếu cần duyệt lại.

## Kịch bản 4 — Xử lý lỗi và khôi phục

- Trong Swagger, thử ID không tồn tại để xem 404; request sai để xem 422.
- Khi giám sát gặp lỗi video/AI/lưu trữ: phiên chuyển ERROR, Web cho đặt lại rồi bắt đầu lại.
- Giải thích `/health` và `/health/ready`; lỗi DB trả 503 kèm request ID.
- Trình bày test hoàn tác khi ghi ảnh/DB thất bại và test ghi đồng thời, không cần ngắt dịch vụ database thật để demo.

## Kịch bản 5 — Bằng chứng kiểm thử

```powershell
.\.venv\Scripts\python.exe -u run_backend_tests.py --browser
```

Lệnh tạo PostgreSQL tạm, chạy kiểm thử backend và thao tác Web tự động bằng Edge ẩn. Server kiểm thử sử dụng AI cố định để kiểm tra backend lặp lại được. Nó không thay model của bản demo, không dùng database hiện có và không chứng minh chất lượng AI.

Mở `results.txt` ở thư mục log được in cuối lệnh. Xem [ma trận kiểm thử](docs/BACKEND_TESTING.md).

## Điểm nhấn khi bảo vệ

- Phân lớp API / service / database.
- State machine phiên và khóa transaction khi chuyển trạng thái.
- Khóa phiên để chống ghi trùng khi nhiều luồng ghi đồng thời.
- Rollback batch và dọn ảnh khi lưu thất bại.
- Validation, SQL tham số, giới hạn đường dẫn bằng chứng.
- Truy vấn có bộ lọc/phân trang, health/readiness, log request ID.
- Kiểm thử tự động trên PostgreSQL thật và nghiệm thu Web.

## Giới hạn được công bố

Chạy local một worker; giám sát gắn với kết nối stream Web. Chưa tích hợp UAV/RTSP thật hoặc phân quyền nhiều người dùng. Độ chính xác AI là giới hạn của nguyên mẫu; không phải tiêu chí chính để chứng minh nghiệp vụ backend đã hoạt động.

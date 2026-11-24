# UAV Weapon Detection — Backend đồ án Công nghệ phần mềm

Hệ thống quản lý phiên giám sát bằng video/webcam, tích hợp YOLO11n, lưu phát hiện và ảnh bằng chứng vào PostgreSQL, cho phép tra cứu và duyệt cảnh báo trên Web. Phạm vi hiện tại: chạy trên laptop, webcam mô phỏng nguồn UAV.

Trọng tâm của đồ án là nghiệp vụ backend, tính toàn vẹn dữ liệu, xử lý lỗi và kiểm thử. Kết quả AI hỗ trợ người dùng xem xét cảnh báo.

## Chạy trên môi trường hiện có

Dùng Python 3.12 trong `.venv`. PostgreSQL phải đang chạy.

1. Cấu hình biến môi trường theo [.env.example](.env.example). Có thể sao chép thành `.env`, điền mật khẩu cục bộ; không đưa tệp này vào kho mã nguồn. Nếu chưa đặt `UAV_PG_PASSWORD`, lệnh khởi tạo và lệnh chạy sẽ hỏi mật khẩu.
2. Khởi tạo hoặc cập nhật schema một lần, **kể cả database cũ**, để bổ sung cột `last_error` và các index:

   ```powershell
   .\.venv\Scripts\python.exe -m backend.database.init_pg
   ```

   Lệnh này không xóa lịch sử hay bảng có sẵn. Tài khoản kết nối cần quyền tạo/đổi cấu trúc bảng; xem SQL trước tại [schema.sql](backend/database/schema.sql).

3. Chạy:

   ```powershell
   .\.venv\Scripts\python.exe run_backend_pg.py
   ```

Mở [Web](http://127.0.0.1:8003/web/) hoặc [Swagger API](http://127.0.0.1:8003/docs). Launcher kiểm tra database/schema và tệp model trước khi chạy.

## Cài trên máy mới

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Tệp requirements ghi phiên bản đang dùng trên máy phát triển. CPU được hỗ trợ; CUDA phụ thuộc bản PyTorch và driver trên máy. Cần mang theo model `models/trained/gks_field_ft_10e/weights/best.pt` và ít nhất một video trong `data/videos`.

Sau khi cài PostgreSQL, mở psql với tài khoản quản trị và tạo database/user nếu chưa có:

```sql
CREATE ROLE uav_backend LOGIN;
\password uav_backend
CREATE DATABASE uav_weapon_detection OWNER uav_backend;
```

Lệnh `\password` là lệnh của psql để nhập mật khẩu ẩn. Với database hiện có, dùng lại tài khoản và thông tin kết nối phù hợp; không chạy lại lệnh tạo role/database. Tiếp tục theo phần chạy môi trường hiện có.

Các biến cấu hình: `UAV_PG_HOST`, `UAV_PG_PORT`, `UAV_PG_DATABASE`, `UAV_PG_USER`, `UAV_PG_PASSWORD`, `UAV_HOST`, `UAV_PORT`. Biến đã đặt trong shell được ưu tiên hơn `.env`.

## Chức năng và quy tắc backend

- Tạo, liệt kê có phân trang, xem và bắt đầu/dừng phiên giám sát.
- Chỉ nhận nguồn `file` trong `data/videos` hoặc camera index 0–99; RTSP chưa được hỗ trợ.
- Kiểm tra nguồn đọc được trước khi chuyển phiên sang `RUNNING`.
- Mỗi phiên chỉ có một luồng giám sát; một camera chỉ thuộc một luồng giám sát tại một thời điểm.
- Khi stream hoạt động: nhận diện → vẽ khung → lưu sự kiện và ảnh JPEG → trả MJPEG.
- Chống lưu trùng cùng nhãn/cùng phiên trong 5 giây; dùng khóa bản ghi PostgreSQL để xử lý các luồng ghi đồng thời.
- Chỉ lưu phát hiện khi phiên còn `RUNNING`, kiểm tra trạng thái trong cùng transaction với thao tác ghi.
- Khi lưu ảnh hoặc cập nhật DB thất bại: rollback batch và dọn ảnh đã tạo trong batch.
- Lỗi giám sát chuyển phiên sang `ERROR`. Dừng/đặt lại để về `STOPPED`, sau đó bắt đầu lại.
- Ngắt kết nối stream kết thúc phiên đang chạy. Nút bắt đầu chỉ chuyển trạng thái; xử lý video diễn ra khi Web mở stream giám sát.
- Tra cứu lịch sử theo phiên, nhãn, trạng thái cảnh báo, khoảng thời gian; phân trang `limit/offset`.
- Xem ảnh bằng chứng; chuyển cảnh báo giữa `NEW`, `CONFIRMED`, `FALSE_POSITIVE`.
- API trả 503 khi database không sẵn sàng; log và header `X-Request-ID` giúp tìm yêu cầu gặp lỗi.

Chạy **một worker** theo launcher vì quyền sở hữu camera/stream được quản lý trong bộ nhớ của tiến trình. Sau khi tiến trình bị tắt đột ngột, phiên có thể còn `RUNNING` trong DB; dừng phiên qua Web/API rồi bắt đầu lại.

## API chính

| API | Mục đích |
| --- | --- |
| `GET /health` | Tiến trình backend đang phản hồi |
| `GET /health/ready` | DB/schema truy vấn được và tệp model tồn tại; chưa đo chất lượng AI |
| `POST /sessions` | Tạo phiên, trạng thái ban đầu STOPPED |
| `GET /sessions?limit=50&offset=0` | Danh sách phiên |
| `GET /sessions/{id}` | Nguồn, trạng thái, thời điểm tạo, lỗi gần nhất |
| `POST /sessions/{id}/start` | Kiểm tra nguồn và bắt đầu |
| `POST /sessions/{id}/stop` | Dừng hoặc đặt lại phiên ERROR |
| `GET /videos/sessions/{id}/monitor` | Stream MJPEG có AI và lưu sự kiện |
| `GET /api/history` | Lịch sử có bộ lọc và phân trang |
| `PATCH /api/alerts/{id}/status` | Duyệt cảnh báo |
| `GET /api/evidence/{id}/image` | JPEG bằng chứng |
| `POST /api/detection/image` | Nhận diện ảnh JPG/PNG binary, tối đa 10 MB |

Ví dụ tạo phiên:

```json
{"source_type": "file", "source": "data/videos/test.mp4"}
```

Ví dụ lọc: `/api/history?label=knife&alert_status=NEW&limit=20&offset=0`. Có thể thêm `session_id`, `date_from`, `date_to` dạng ISO 8601. Thời gian không có múi giờ được hiểu là UTC. Response giữ các trường cũ và bổ sung `total`, `limit`, `offset`.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -u run_backend_tests.py
.\.venv\Scripts\python.exe -u run_backend_tests.py --browser
```

Runner tìm PostgreSQL trong PATH hoặc thư mục cài thông dụng; có thể truyền `--pg-bin "D:\PostgreSQL\18\bin"`. Nó tạo cluster/database tạm trên cổng localhost riêng, chạy test rồi dừng và xóa cluster đã tạo. Không kết nối đến database đang dùng để demo. Log được giữ trong `runtime/test-runs/<run>/`.

`--browser` dùng Microsoft Edge ở chế độ ẩn. Test Web dùng AI cố định trong **server dành riêng cho kiểm thử**, kiểm tra luồng tạo phiên → giám sát video → lưu DB/ảnh → xem ảnh → duyệt/lọc cảnh báo. Bản chạy `run_backend_pg.py` vẫn dùng model thật.

Xem [thiết kế backend](docs/BACKEND_DESIGN.md), [ma trận kiểm thử](docs/BACKEND_TESTING.md) và [kịch bản demo](DEMO_BACKEND.md).

## Cấu trúc

Khi đưa lên GitHub, `.gitignore` giữ model dùng bởi backend và video `test.mp4`, đồng thời loại `.env`, môi trường `.venv`, database, ảnh bằng chứng, dataset và các kết quả huấn luyện. Mỗi thành viên tự cài thư viện, cấu hình `.env` và khởi tạo PostgreSQL theo hướng dẫn ở trên. Bộ dữ liệu huấn luyện không đi kèm bản clone.

- `backend/api`: HTTP, validation và mã lỗi.
- `backend/services`: nghiệp vụ phiên, video, lịch sử, cảnh báo và ảnh.
- `backend/database`: kết nối, SQL schema, công cụ khởi tạo.
- `frontend`: giao diện thao tác các API.
- `tests`: kiểm thử backend hiện tại với PostgreSQL thật.
- `project_archive`: script huấn luyện, đánh giá và tiện ích cũ; không phải test suite hiện tại.
- `models`, `data`, `runtime`: model, dữ liệu và tệp sinh khi chạy.

# 🏸 ShuttleSplit — Quản lý chi phí cầu lông

## Cài đặt nhanh (Development)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Mở: **http://127.0.0.1:8000**

---

## Triển khai Production (Docker)

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## Tài khoản demo

| Username | Password | Vai trò | Số dư |
|---|---|---|---|
| `duong` | `123456` | **Chủ nhóm** | +887,500đ |
| `nam` | `123456` | Thành viên | +320,833đ |
| `hung` | `123456` | Thành viên | +120,833đ |
| `linh` | `123456` | Thành viên | **-112,500đ (nợ)** |
| `minh` | `123456` | Thành viên | **-106,667đ (nợ)** |
| `admin` | `admin123` | Superuser | — |

---

## Tính năng đầy đủ

### Quản lý nhóm & thành viên
- ✅ Tạo nhóm cầu lông với thông tin ngân hàng
- ✅ Mã mời tự động (8 ký tự) để thành viên tham gia
- ✅ Chủ nhóm tạo tài khoản trực tiếp cho thành viên
- ✅ Sửa/xóa thành viên
- ✅ Phân quyền Host / Member

### Quản lý buổi chơi
- ✅ Tạo buổi với: tiền sân, tiền cầu, tiền nước, chi phí khác
- ✅ Tick chọn thành viên tham gia
- ✅ Tự động chia đều chi phí
- ✅ Preview chi phí realtime khi nhập

### Quản lý ví & công nợ
- ✅ Mỗi thành viên có ví riêng per nhóm
- ✅ Tự động trừ tiền khi tham gia buổi chơi
- ✅ Nếu số dư âm → hiển thị công nợ
- ✅ Chủ nhóm ghi nhận nạp tiền
- ✅ Lịch sử giao dịch chi tiết

### Thanh toán
- ✅ Thành viên gửi yêu cầu thanh toán + upload biên lai
- ✅ Email tự động gửi cho chủ nhóm
- ✅ Chủ nhóm xác nhận/từ chối
- ✅ Email xác nhận gửi cho thành viên

### Email tự động (Celery)
- ✅ Nhắc nợ khi công nợ > 200,000đ
- ✅ Nhắc nợ khi nợ > 30 ngày
- ✅ Kèm thông tin chuyển khoản đầy đủ

### Dashboard
- ✅ Dashboard Host: tổng quan nhóm, danh sách nợ
- ✅ Dashboard Member: số dư, lịch sử tham gia, lịch sử thanh toán
- ✅ Báo cáo công nợ toàn nhóm

---

## Cấu trúc project

```
badminton/
├── accounts/          # Custom User model
├── groups/            # Group, GroupMember + views
├── sessions_app/      # BadmintonSession, SessionParticipant + services
├── wallet/            # Wallet, WalletTransaction + services
├── payments/          # Payment, PaymentProof + views
├── notifications/     # EmailNotification, Celery tasks
├── templates/         # HTML templates (Django Template)
├── static/css/        # Stylesheet
├── config/            # Settings, URLs, Celery config
├── docker-compose.yml
├── Dockerfile
└── nginx.conf
```

## Cấu hình Email (Gmail SMTP)

Thêm vào `.env` hoặc environment variables:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=ShuttleSplit <your@gmail.com>
```

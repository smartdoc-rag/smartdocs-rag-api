# SmartDoc AI API

Backend API cho dự án SmartDoc AI, xây dựng bằng Django + Django REST Framework theo mô hình tách lớp (API -> Services -> Repositories -> Models).

## 1. Yêu cầu môi trường

- Python 3.11+
- PostgreSQL
- Redis (nếu bật cache/rate limit liên quan)

## 2. Cài đặt nhanh

1. Clone dự án.
2. Tạo virtual environment.
3. Cài dependencies.
4. Tạo file môi trường từ `.env.example`.
5. Chạy migrate.
6. Chạy server.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python run.py
```

Lưu ý:

- Script `run.py` sẽ dọn `__pycache__` trước khi start server.
- Có thể chạy bằng lệnh Django mặc định: `python manage.py runserver`.

## 3. Cấu hình môi trường

Các biến quan trọng trong `.env`:

- `SECRET_KEY`
- `DEBUG`
- `DJANGO_ENV`
- `DATABASE_URL_DEV`
- `DATABASE_URL_PROD`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `ALLOWED_HOSTS`

## 4. Luồng làm việc Git (tóm tắt)

Nguyên tắc chính:

- Mỗi người làm việc dựa trên `dev`.
- Mỗi nhánh chỉ làm một chức năng.
- Trước khi push phải rebase nhánh đang làm việc lên `dev` mới nhất.
- Commit phải tách nhỏ, rõ mục đích.

Luồng chuẩn **(đảm bảo đã thực hiện add và commit ở working-branch)**:

```bash
git checkout dev
git pull origin dev
git checkout <working-branch>
git rebase dev
git push origin <working-branch>
```

Nếu vừa rebase xong và remote đã có lịch sử cũ của nhánh, dùng:

```bash
git push --force-with-lease origin <working-branch>
```

## 5. Quy tắc commit

Định dạng commit:

```text
<type>(<scope>): <subject>
```

Ví dụ:

```text
feat(user): add login endpoint validation
fix(refresh_token): handle expired token cleanup
refactor(document): simplify repository query path
```

Backend scope bắt buộc là tên model (ví dụ: `user`, `refresh_token`, `document`, `question`).

Xem quy định đầy đủ tại `CONTRIBUTING.md`.

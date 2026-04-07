# Contributing Guide

Tài liệu này quy định cách làm việc Git cho team để giữ lịch sử sạch, dễ review và hạn chế conflict.

## 1. Branching strategy

- `main`: chỉ nhận code đã ổn định.
- `dev`: nhánh tích hợp cho toàn team.
- Nhánh chức năng: mỗi nhánh chỉ xử lý một chức năng hoặc một bug.

Quy tắc:

- Không commit trực tiếp lên `main`.
- Không push code chưa hoàn thiện lên `dev`.
- Mọi công việc đều bắt đầu từ `dev` mới nhất.

## 2. Đặt tên nhánh

Mẫu khuyến nghị:

- `feat/<feature-name>`
- `fix/<bug-name>`
- `refactor/<target>`

Ví dụ:

- `feat/user-login`
- `fix/refresh-token-expired`
- `refactor/document-repository`

## 3. Luồng làm việc bắt buộc

Trước khi bắt đầu làm tính năng:

```bash
git checkout dev
git pull origin dev
git checkout -b <working-branch>
```

Trong quá trình làm:

- Commit nhỏ, tách theo từng mục đích.
- Không gộp nhiều chức năng lớn vào một commit.

Trước khi push nhánh đang làm việc **(đảm bảo đã thực hiện add và commit ở working-branch)**:

```bash
git checkout dev
git pull origin dev
git checkout <working-branch>
git rebase dev
```

Sau đó push:

```bash
git push origin <working-branch>
git push origin -u <working-branch> # Cho lần push đầu tiên
```

Nếu nhánh đã push trước đó và vừa rebase lại lịch sử:

```bash
git push --force-with-lease origin <working-branch>
```

## 4. Commit rules

### 4.1 Cú pháp commit

```text
<type>(<scope>): <subject>
```

### 4.2 Các type được dùng

- `feat`: thêm tính năng mới.
- `fix`: sửa lỗi.
- `refactor`: cải tiến code không đổi hành vi.
- `test`: thêm hoặc sửa test.
- `docs`: cập nhật tài liệu.
- `chore`: việc kỹ thuật/phụ trợ.

### 4.3 Quy tắc scope cho backend

- Với thay đổi backend business logic, scope bắt buộc là tên model.
- Dùng tên model ở dạng chữ thường và nhất quán theo codebase.
- Một commit chỉ nên tập trung vào một model chính.

Ví dụ scope hợp lệ:

- `user`
- `refresh_token`
- `document`
- `question`

### 4.4 Quy tắc subject

- Viết ngắn gọn, mô tả hành động.
- Dùng tiếng Anh để thống nhất lịch sử commit.
- Không kết thúc bằng dấu chấm.

Ví dụ commit tốt:

```text
feat(user): add register input validation
fix(refresh_token): reject reused refresh token
refactor(document): move search logic to service layer
```

Ví dụ commit chưa đạt:

```text
update code
fix: bug
feat(api): do many things
```

## 5. Quy tắc tách commit

- Tách commit theo mục đích kỹ thuật, không theo số lượng file.
- Tách riêng commit format/lint khỏi commit logic.
- Tách migration, business logic, và tài liệu khi có thể.
- Không trộn sửa nhiều model trong cùng một commit nếu không thật sự cần.

## 6. Pull request vào dev

Checklist trước khi tạo PR:

- Đã rebase lên `dev` mới nhất.
- Không còn conflict.
- Commit message đúng chuẩn `type(scope): subject`.
- Scope backend đúng theo model liên quan.
- PR chỉ chứa thay đổi thuộc một chức năng chính.

## 7. Tạo Pull Request (PR)

Sau khi đã push nhánh lên remote, bạn cần tạo PR để merge code vào `dev`.

1.  Truy cập vào repository trên giao diện web (GitHub, GitLab, etc.).
2.  Hệ thống thường sẽ tự động gợi ý tạo PR từ nhánh bạn vừa push.
3.  Nhấn vào nút "Compare & pull request".
4.  **Quan trọng:**
    -   **Base branch** (nhánh gốc) phải là `dev`.
    -   **Compare branch** (nhánh so sánh) là nhánh bạn đang làm việc.
5.  **Đặt tên PR:** Tên PR nên trùng với tên nhánh làm việc của bạn.
    -   Ví dụ, nếu nhánh là `feat/user-login`, tên PR cũng là `feat/user-login`.
6.  Kiểm tra lại checklist trong mô tả PR và tạo PR.

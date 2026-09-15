---
title: Tin Hoc Trac Nghiem
emoji: 📝
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Web Trắc Nghiệm - 40 câu / 30 phút

## Cấu trúc project
```
quizapp/
├── app.py              # Flask server (logic chính)
├── questions.json      # Dữ liệu câu hỏi + đáp án (lấy từ file đề bạn gửi)
├── templates/
│   ├── index.html       # Trang bắt đầu
│   ├── quiz.html         # Trang làm bài (có đồng hồ đếm ngược)
│   └── result.html       # Trang kết quả + xem lại đáp án
├── static/
│   └── style.css
└── requirements.txt
```

## Cách chạy trên VS Code

1. Mở thư mục `quizapp` bằng VS Code.
2. Mở Terminal (Ctrl + `) và cài thư viện:
   ```
   pip install -r requirements.txt
   ```
3. Chạy server:
   ```
   python app.py
   ```
4. Mở trình duyệt vào: http://127.0.0.1:5000

## Tuỳ chỉnh
- Đổi số câu hỏi mỗi lượt thi: sửa `NUM_QUESTIONS` trong `app.py` (mặc định 40).
- Đổi thời gian làm bài: sửa `TIME_LIMIT_SECONDS` trong `app.py` (mặc định 1800 giây = 30 phút).
- Thêm/sửa câu hỏi: chỉnh trực tiếp file `questions.json`, mỗi câu có dạng:
  ```json
  {
    "id": 1,
    "question": "Nội dung câu hỏi ?",
    "options": {"a": "...", "b": "...", "c": "...", "d": "..."},
    "answer": "b"
  }
  ```
- Đổi `secret_key` trong `app.py` trước khi dùng thật (dòng `app.secret_key = ...`).

## Cách hoạt động
- Mỗi lần bấm "Bắt đầu làm bài", hệ thống lấy ngẫu nhiên 40 câu (hoặc hết nếu ít hơn) và xáo trộn thứ tự đáp án a/b/c/d.
- Đồng hồ đếm ngược 30:00 chạy bằng JavaScript; hết giờ tự động nộp bài.
- Nộp bài xong sẽ hiện điểm số và xem lại từng câu: đáp án đúng, đáp án bạn chọn.

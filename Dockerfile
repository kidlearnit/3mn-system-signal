# 1. Base image
FROM python:3.11-slim

# 2. Cài đặt gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
	build-essential \
	default-libmysqlclient-dev \
	pkg-config \
	&& rm -rf /var/lib/apt/lists/*

# 3. Đặt thư mục làm việc
WORKDIR /code

# 4. Copy requirements và cài đặt Python packages
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy backend code vào container
COPY . .

# 6. Biến môi trường chung
ENV PYTHONUNBUFFERED=1

# 7. Lệnh mặc định (cho service web)
CMD ["python", "-m", "flask", "--app", "app.init", "run", "--host=0.0.0.0", "--port=5000"]

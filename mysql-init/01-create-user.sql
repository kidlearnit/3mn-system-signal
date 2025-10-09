-- Tạo user trader (nếu chưa tồn tại)
CREATE USER IF NOT EXISTS 'trader'@'%' IDENTIFIED BY 'traderpass';

-- Cấp toàn quyền trên database trading_db
GRANT ALL PRIVILEGES ON trading_db.* TO 'trader'@'%';

-- Áp dụng thay đổi
FLUSH PRIVILEGES;

# 專案 Docker 化指南

## 專案結構
```
ewhiteboard/
├── .env                    # 環境變數設定（敏感資訊）
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile              # Django 應用的 Docker 配置
├── requirements.txt        # Python 依賴清單
├── manage.py               # Django 管理腳本
├── ewhiteboard/            # 主專案目錄
├── users/                  # 用戶應用
├── projects/               # 專案應用
├── boards/                 # 白板應用
└── nginx/                  # Nginx 配置
    ├── Dockerfile          # Nginx 的 Docker 配置
    └── nginx.conf          # Nginx 伺服器配置
```

## 環境設置

1. 複製 `.env.example` 檔案並命名為 `.env`，根據您的環境調整設定：
   ```bash
   cp .env.example .env
   ```

2. 修改 `.env` 檔案中的敏感資訊，特別是：
   - `SECRET_KEY`: Django 密鑰（建議使用隨機生成的字串）
   - `POSTGRES_PASSWORD`: 資料庫密碼
   - 生產環境的域名設定

## 開發環境部署

使用 Docker Compose 啟動開發環境：

```bash
docker-compose up -d
```

這將啟動三個服務：
- PostgreSQL 資料庫
- Django 應用（開發伺服器）
- Nginx 伺服器（靜態檔案）

訪問 http://localhost:8000 可以查看應用程式。

## 生產環境設置

生產環境需要額外的安全設定：

1. 確保 `.env` 檔案中的 `DEBUG=False`
2. 更新 `ALLOWED_HOSTS` 添加您的域名
3. 生成新的隨機 `SECRET_KEY`
4. 設置更強的資料庫密碼

然後使用以下命令啟動：

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 資料庫管理

初次部署時，需要執行遷移並創建超級用戶：

```bash
# 執行遷移
docker-compose exec web python manage.py migrate

# 創建超級用戶
docker-compose exec web python manage.py createsuperuser
```

## 備份與還原

備份資料庫：

```bash
docker-compose exec db pg_dump -U ewhiteboard_user ewhiteboard > backup.sql
```

還原資料庫：

```bash
cat backup.sql | docker-compose exec -T db psql -U ewhiteboard_user -d ewhiteboard
```

## 更新部署

更新代碼後，重新建構容器：

```bash
docker-compose down
docker-compose up -d --build
```

## 檢視日誌

檢視應用程式日誌：

```bash
docker-compose logs -f web
```

檢視資料庫日誌：

```bash
docker-compose logs -f db
```

## 疑難排解

如遇問題，請檢查：
1. 容器狀態： `docker-compose ps`
2. 容器日誌： `docker-compose logs`
3. 網路連接： `docker network ls`
4. 確認環境變數是否正確載入
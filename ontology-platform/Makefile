.PHONY: install run test docker-build docker-run

# 默认目标
all: install

# 安装依赖
install:
	@echo "Installing dependencies..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Installing Python packages..."
	@./venv/bin/pip install -r requirements.txt
	@echo "Installation complete!"

# 运行项目
run:
	@echo "Starting the application..."
	@./venv/bin/python supervisor.py

# 运行测试
test:
	@echo "Running tests..."
	@./venv/bin/python -m pytest -v || ./venv/bin/python -m unittest discover -v

# Docker 构建
docker-build:
	@echo "Building Docker image..."
	@docker build -t ontology-platform:latest .

# Docker 运行
docker-run:
	@echo "Running Docker container..."
	@docker-compose up -d

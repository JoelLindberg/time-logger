APP_NAME=time-logger
DOCKER_IMAGE=time-logger:latest
UID := $(shell id -u)
GID := $(shell id -g)
SUDO_USER := $(SUDO_USER)
SUDO_UID := $(SUDO_UID)
SUDO_GID := $(SUDO_GID)

run: docker-build
	@echo "🚀 Running container..."
	@if [ -z $$SUDO_USER ];\
	then \
		export CURRENT_UID=$(UID):$(GID) && docker compose -f compose.yml up;\
	else \
		export CURRENT_UID=$(SUDO_UID):$(SUDO_GID) && docker compose -f compose.yml up;\
	fi \

docker-build: clean
	@echo "🔨 Building Docker image..."
	@docker build -t $(DOCKER_IMAGE) .

clean: db
	@echo "🔄 Removing old docker image and containers that are using it"
	@containers=$$(docker ps -a | grep 'time-logger' | awk '{print $$1}'); \
    if [ -n "$$containers" ]; then \
        echo "Removing containers based on 'time-logger' image..."; \
        echo "$$containers" | xargs docker rm; \
    else \
        echo "No matching containers found. Nothing to remove."; \
    fi
	@echo "Removing old images"
	@docker rmi $(DOCKER_IMAGE) -f

db:
	@echo "📁 Creating sqlite database directory"
	@if [ ! -d "./db" ];\
	then \
		mkdir ./db;\
		if [ -z $$SUDO_USER ];\
		then \
			chown $(UID):$(GID) db;\
		else \
			chown $(SUDO_UID):$(SUDO_GID) db;\
		fi \
	fi

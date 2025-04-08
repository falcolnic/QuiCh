.PHONY: build run dev stop clean logs

build:
	docker compose build

dev:
	docker compose up

run:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down --rmi all --volumes --remove-orphans
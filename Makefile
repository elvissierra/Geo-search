#
# Geo Search API
#

a_if_api_container=geo_search_api

.PHONY: help
help:
	@echo 'Makefile of Geo Search API'
	@echo '---'
	@echo ''
	@echo '1. up_development'
	@echo ''
	@echo '   Runs the Geo Search API application as a docker compose service in the development '
	@echo '   mode. NOTE: this command must be executed on the host machine of developer.'
	@echo ''
	@echo '   Usage:  make up_development'
	@echo ''
	@echo '2. build_for_development'
	@echo ''
	@echo '   Builds the docker images of the Geo Search API service ready to use for the '
	@echo '   development. NOTE: this command must be executed on the host machine of developer.'
	@echo ''
	@echo '   Usage:  make build_for_development'
	@echo ''
	@echo '3. prune'
	@echo ''
	@echo '   Removes the docker containers, volumes and networks. NOTE: this command must be '
	@echo '   executed on the host machine of developer.'
	@echo ''
	@echo '   Usage:  make prune'
	@echo ''
	@echo '4. pre_commit'
	@echo ''
	@echo '   Execute the pre-commit source code checks: black and ruff linter. NOTE: this command must '
	@echo '   be executed on the host machine of developer.'
	@echo ''
	@echo '   Usage:  make pre_commit'
	@echo ''
	@echo '5. ci_run_tests'
	@echo ''
	@echo '   This command runs the unit tests. It used during CI/CD process. NOTE: this command '
	@echo '   must be executed inside a docker container.'
	@echo ''
	@echo '   Usage:  make ci_run_tests'
	@echo ''
	@echo '6. ci_check_code_quality'
	@echo ''
	@echo '   This command checks the code quality using black and ruff linter tools. It used during '
	@echo '   CI/CD process. NOTE: this command must be executed inside a docker container.'
	@echo ''
	@echo '   Usage:  make ci_check_code_quality'
	@echo ''
	@echo '7. docker_entrypoint_development'
	@echo ''
	@echo '   The entry point of a docker container in the development mode.'
	@echo ''
	@echo '   Usage:  make docker_entrypoint_development'
	@echo ''
	@echo '8. docker_entrypoint_production'
	@echo ''
	@echo '   The entry point of a docker container in the production mode.'
	@echo ''
	@echo '   Usage:  make docker_entrypoint_production'
	@echo ''

.PHONY: up_development
up_development:
	docker-compose --project-name geo_search --file docker-compose.yml --env-file .env up -d

.PHONY: build_for_development
build_for_development:
	docker build --target development --file Dockerfile --tag geo-search/api:development.latest .


.PHONY: up_production
up_production:
	docker-compose --project-name geo_search --file docker-compose.yml --file docker-compose.production.yml --env-file .env up -d

.PHONY: build_for_production
build_for_production:
	docker build --target production --file Dockerfile --tag geo-search/api:production.latest .


.PHONY: prune
prune:
	@docker-compose --project-name geo_search -f docker-compose.yml -f docker-compose.production.yml down -v

.PHONY: pre_commit
pre_commit:
	docker exec -it ${a_if_api_container} sh -ic 'python3 -m black --line-length=100 .'
	docker exec -it ${a_if_api_container} sh -ic 'python3 -m ruff --fix ./geo_search_api/*'

.PHONY: ci_run_tests
ci_run_tests:
	python3 -m pytest -vvv --cov=geo_search_api --cov-report xml --cov-fail-under=95 --cov-report term-missing:skip-covered

.PHONY: ci_check_code_quality
ci_check_code_quality:
	python3 -m black --check --line-length 100 .
	python3 -m ruff check ./geo_search_api/*

.PHONY: docker_entrypoint_development
docker_entrypoint_development:
	@echo -e "\033[32m>> 1. Run migrations:\033[m"
	@python3 manage.py migrate
	@echo -e "\033[32m>> 2. Start API development server:\033[m"
	@python manage.py runserver 0.0.0.0:8000

.PHONY: docker_entrypoint_production
docker_entrypoint_production:
	@echo -e "\033[32m>> 1. Run migrations:\033[m"
	@python3 manage.py migrate
	@echo -e "\033[32m>> 2. Start API production server:\033[m"
	@python3 -m gunicorn --timeout 0

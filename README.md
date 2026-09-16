# Geo Search
Main Geo Search service API backend.

## Endpoints
- api/health_check/ - endpoint for checking service health.
- api/notes/ - endpoint for working with Post, Idea, Comment entities.
- api/storage/ - endpoint for working with s3 bucket presigned urls.
- api/opensearch/ - endpoint for working with OpenSearch inside project AWS VPC.
- api/swagger/ - endpoint with swagger API documentation (works in all environments except PROD)

## Environment Variables
1. Create a copy of `.env.example` file:
  ```shell
  cp .env.example .env
  ```
2. Environment variables need to be created for the following and formated with spaces to be replaced with _ , ex. DB_NAME=geo_search
https://docs.docker.com/compose/environment-variables/


- CURRENT_ENVIRONMENT - set one of the supported environments:
```
"gitlab_unit_tests"
"local_unit_tests"
"local_do_not_validate_token"
"local_validate_token"
"local_docker"
"dev"
"stage"
"prod"
```
- AWS_LOAD_BALANCER_URL - load balancer public url (needs because of CORS)
- DJANGO_SECRET_KEY - secret key (required for production environment)
- DB_HOST - postgresql database host
- DB_PORT - postgresql database port
- DB_NAME - postgresql database name
- DB_USERNAME - aws secret arn where database username is stored
- DB_PASSWORD - aws secret arn where database password is stored
- AWS_OPENSEARCH_HOST - opensearch database host
- CLOUDWATCH_LOG_GROUP - aws cloudwatch log group name
- CLOUDWATCH_STREAM_NAME - aws cloudwatch log stream name
- AUTH0_DOMAIN - Auth0 domain
- AUTH0_ISSUER - Auth0 issuer
- AUTH0_API_AUDIENCE - Auth0 API audience

## Run the project

### Run locally using docker-compose
1. Install `docker` and `docker-compose`
2. Create a copy of `.env.example` file:
  ```shell
  cp .env.example .env
  ```
3. Build the docker images:
  ```shell
  make build_for_development
  ```
4. Run an application:
  ```shell
  make up_development
  ```
5. Access application via http://localhost:8000 address.

### Virtual Environment (not recommended)

1. install (virtualenv)[https://pypi.org/project/virtualenv/]
2. create a virtual environment with python3.10
3. activate the environment
4. install project dependencies
```shell
pip install -r requirements/dev.txt
```
- Start postgres docker image.
```
docker run --name myPostgresDb -p 5455:5432 -e POSTGRES_USER=postgresUser -e POSTGRES_PASSWORD=postgresPW -e POSTGRES_DB=postgresDB -d postgres
```
- Export all required environment variables.
```
export CURRENT_ENVIRONMENT=local_do_not_validate_token DB_HOST=localhost ...
```
- Run migrations:
```
./manage.py migrate
```
- Start server:
```
./manage.py runserver
```
- Access application via `http://127.0.0.1:8000` address.

## Git Flow

Git flow is described (here)[https://studio-x.atlassian.net/wiki/spaces/IF/pages/2139258881/Git+Flow]
Branch and commit rules are enforced according to the documentation

## Django

Current application using (Django 4.0.8)[https://docs.djangoproject.com/en/4.0/]

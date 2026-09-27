FROM python:3.10-alpine as base

RUN apk add --update --no-cache --virtual .tmp-build-deps \
    --repository https://dl-cdn.alpinelinux.org/alpine/v3.18/main \
    gcc=12.2.1_git20220924-r10 \
    libc-dev=0.7.2-r5 \
    linux-headers=6.3-r0 \
    postgresql14-dev=14.10-r0

RUN apk add --no-cache libffi-dev=3.4.4-r2 \
    --repository https://dl-cdn.alpinelinux.org/alpine/v3.18/main \
    make=4.4.1-r1 \
    libpq=15.5-r0 \
    expat=2.5.0-r1

# Add non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Set default build-env variable
ARG BUILD_ENV=dev

# Upgrade pip
RUN pip install --upgrade --no-cache-dir pip==22.3.1
# Install dependencies
COPY ./requirements requirements/
RUN pip install --user --no-cache-dir -r requirements/${BUILD_ENV}.txt

# Clean up
USER root
RUN apk del .tmp-build-deps
USER appuser

WORKDIR /app

COPY ./manage.py manage.py
COPY ./middlewares middlewares
COPY ./utils.py utils.py
COPY ./clients clients
COPY ./gunicorn.conf.py gunicorn.conf.py
COPY ./Makefile Makefile
COPY ./geo_search_api geo_search_api


FROM base as development

USER appuser
HEALTHCHECK --interval=5m --timeout=3s CMD wget -nv -t1 --spider http://localhost:8000/api/health_check/cluster || exit 1
EXPOSE 8000
ENTRYPOINT ["make", "docker_entrypoint_development"]


# This section added for the future usage. It will replaced with running
# gunicorn
FROM base as production

USER appuser
HEALTHCHECK --interval=5m --timeout=3s CMD wget -nv -t1 --spider http://localhost:8000/api/health_check/cluster || exit 1
EXPOSE 8000
ENTRYPOINT ["make", "docker_entrypoint_production"]

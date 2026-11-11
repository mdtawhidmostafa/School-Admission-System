#!/bin/sh
set -eu
API_BASE_URL="${API_BASE_URL:-/api}"
printf 'window.__APP_CONFIG__ = { apiBaseUrl: "%s" };\n' "$API_BASE_URL" > /usr/share/nginx/html/config.js

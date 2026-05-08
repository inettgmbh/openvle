#!/bin/sh

ROOT_DIR=/usr/share/nginx/html
ENV_FILE=/docker-entrypoint.d/.env

# Function to trim spaces around '=' and remove quotes
trim_and_export() {
  local line="$1"
  local key
  local value

  # Remove leading and trailing spaces
  line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  # Check if line contains '='
  if echo "$line" | grep -q '='; then
    # Extract key and value
    key=$(echo "$line" | cut -d '=' -f 1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    value=$(echo "$line" | cut -d '=' -f 2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Remove surrounding quotes
    value=$(echo "$value" | sed "s/^'\(.*\)'$/\1/;s/^\"\(.*\)\"$/\1/")

    # Export environment variable
    export "$key=$value"
  fi
}

# Load environment variables from .env file, skipping empty lines and comments
if [ -f "$ENV_FILE" ]; then
  buffer=""
  while IFS= read -r line || [ -n "$line" ]; do
    # Append line to buffer (if there's no newline at the end, the buffer handles the last line)
    buffer="$line"
    
    # Skip empty lines and lines starting with #
    if [ -n "$buffer" ] && [ "${buffer:0:1}" != "#" ]; then
      trim_and_export "$buffer"
    fi
  done < "$ENV_FILE"
fi

# Replace env vars in files served by NGINX
for file in $ROOT_DIR/*/*.js* $ROOT_DIR/*.js* $ROOT_DIR/*.html; do
  if [ -f "$file" ]; then
    # Replace each environment variable placeholder
    for key in $(env | grep '^VITE_' | cut -d '=' -f 1); do
      value=$(eval echo \$$key)
      sed -i "s|${key}_PLACEHOLDER|${value}|g" $file
    done
  fi
done

# Let container execution proceed
exec "$@"

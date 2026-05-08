#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT="openvle-backend"
VERSION=$(grep -E '^version[[:space:]]*=' "$CODE_DIR/pyproject.toml" | head -1 | sed -E 's/^version[[:space:]]*=[[:space:]]*"(.*)"$/\1/')
COPYRIGHT_HOLDER="inett GmbH"
BUGS_ADDRESS="support@inett.de"
LANGUAGE_TEAM="inett GmbH <support@inett.de>"

# Portable sed -i (macOS vs Linux)
sed_inplace() {
    if [[ "$OSTYPE" == darwin* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

usage() {
    echo "Usage: $0 {extract|update|compile|all}"
    echo ""
    echo "Commands:"
    echo "  extract   Extract translatable strings into messages.pot"
    echo "  update    Update .po files from messages.pot"
    echo "  compile   Compile .po files into .mo binaries"
    echo "  all       Run extract, update, and compile in sequence"
    exit 1
}

cmd_extract() {
    echo "Extracting translatable strings..."
    (cd "$CODE_DIR" && pybabel extract \
        -F babel.cfg \
        -o translations/messages.pot \
        --project="$PROJECT" \
        --version="$VERSION" \
        --copyright-holder="$COPYRIGHT_HOLDER" \
        --msgid-bugs-address="$BUGS_ADDRESS" \
        .)
    # Set metadata to internal defaults
    sed_inplace \
        -e "s|Language-Team: LANGUAGE <LL@li.org>|Language-Team: $LANGUAGE_TEAM|" \
        -e "s|Last-Translator: FULL NAME <EMAIL@ADDRESS>|Last-Translator: $LANGUAGE_TEAM|" \
        -e "s|FIRST AUTHOR <EMAIL@ADDRESS>, .*|Sascha Zinn <szinn@inett.de>, 2025.|" \
        -e '/^"PO-Revision-Date:.*$/d' \
        "$CODE_DIR/translations/messages.pot"
    echo "Done: translations/messages.pot"
}

cmd_update() {
    echo "Updating .po files..."
    pybabel update \
        -i "$CODE_DIR/translations/messages.pot" \
        -d "$CODE_DIR/translations"
    # Sync metadata from POT into all .po files (pybabel update does not propagate these)
    local revision_date
    revision_date=$(date +"%Y-%m-%d %H:%M%z")
    for po in "$CODE_DIR"/translations/*/LC_MESSAGES/messages.po; do
        sed_inplace \
            -e "s|FIRST AUTHOR <EMAIL@ADDRESS>, .*|Sascha Zinn <szinn@inett.de>, 2025.|" \
            -e "s|^\"Project-Id-Version: .*|\"Project-Id-Version: $PROJECT $VERSION\\\n\"|" \
            -e "s|^\"Report-Msgid-Bugs-To: .*|\"Report-Msgid-Bugs-To: $BUGS_ADDRESS\\\n\"|" \
            -e "s|^\"Last-Translator: .*|\"Last-Translator: $LANGUAGE_TEAM\\\n\"|" \
            -e "s|^\"Language-Team: .*|\"Language-Team: $LANGUAGE_TEAM\\\n\"|" \
            -e "s|^\"PO-Revision-Date: .*|\"PO-Revision-Date: $revision_date\\\n\"|" \
            "$po"
    done
    echo "Done: .po files updated"
}

cmd_compile() {
    echo "Compiling .mo files..."
    pybabel compile -d "$CODE_DIR/translations"
    echo "Done: .mo files compiled"
}

case "${1:-}" in
    extract) cmd_extract ;;
    update)  cmd_update ;;
    compile) cmd_compile ;;
    all)     cmd_extract; cmd_update; cmd_compile ;;
    *)       usage ;;
esac

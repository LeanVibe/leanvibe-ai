#!/usr/bin/env bash
# LeanVibe repo pre-push credential scan (fast, low-noise)
# - Scans changed (staged) files by default
# - Fallback to all tracked files when STRICT_PREPUSH=1
# - Tiny allowlist for docs/examples placeholder values

set -euo pipefail

# Go to repo root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Determine target files
if [[ "${STRICT_PREPUSH:-0}" == "1" ]]; then
  mapfile -t CANDIDATE_FILES < <(git ls-files)
else
  mapfile -t CANDIDATE_FILES < <(git diff --cached --name-only --diff-filter=ACMR || true)
fi

if [[ ${#CANDIDATE_FILES[@]} -eq 0 ]]; then
  echo "[pre-push] No files to scan. Skipping."
  exit 0
fi

# Restrict to text-like files only (ignore binaries by extension heuristic)
FILTERED_FILES=()
for f in "${CANDIDATE_FILES[@]}"; do
  [[ ! -f "$f" ]] && continue
  case "$f" in
    *.png|*.jpg|*.jpeg|*.gif|*.webp|*.ico|*.pdf|*.zip|*.gz|*.tgz|*.xz|*.bin|*.mov|*.mp4|*.wav|*.aiff|*.ttf|*.otf)
      continue;;
    *)
      FILTERED_FILES+=("$f");;
  esac
done

if [[ ${#FILTERED_FILES[@]} -eq 0 ]]; then
  echo "[pre-push] No text files to scan. Skipping."
  exit 0
fi

# Secret patterns (conservative set to reduce false positives)
SECRET_REGEX=(
  'AWS_SECRET_ACCESS_KEY|aws_secret_access_key'
  'AKIA[0-9A-Z]{16}'
  'ASIA[0-9A-Z]{16}'
  '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
  'xox[abpr]-[0-9A-Za-z-]+'
  'api(_|-)key\s*[:=]\s*[A-Za-z0-9_\-]{16,}'
  'password\s*[:=]'
  'secret\s*[:=]'
)

# Allowlist patterns used only when the file lives under docs/** or **/examples/**
DOCS_ALLOWLIST=(
  'password=example'
  'your-client-secret'
  'YOUR/WEBHOOK/URL'
  'your-webhook-secret'
  'your-secret-key'
  'example@example.com'
  'sk_test_'
  'sk_live_'
  'whsec_'
)

had_findings=0

scan_file() {
  local file="$1"
  local is_docs=0
  if [[ "$file" == docs/* || "$file" == */examples/* ]]; then
    is_docs=1
  fi

  # Use git grep to leverage repo attributes and ignore binary (-I)
  for rx in "${SECRET_REGEX[@]}"; do
    # shellcheck disable=SC2046
    if git grep -nI -E -- "$rx" -- "$file" >/tmp/lv_hits.$$ 2>/dev/null; then
      while IFS= read -r hit; do
        local line_text
        line_text="${hit#*:}"
        if [[ $is_docs -eq 1 ]]; then
          local allowed=0
          for allow in "${DOCS_ALLOWLIST[@]}"; do
            if grep -E -q -- "$allow" <<<"$line_text"; then
              allowed=1; break
            fi
          done
          if [[ $allowed -eq 1 ]]; then
            continue
          fi
        fi
        if [[ $had_findings -eq 0 ]]; then
          echo ""
          echo "Potential credential leaks detected:"
          echo "------------------------------------"
        fi
        had_findings=1
        echo "${file}: ${hit#*:}"
      done < /tmp/lv_hits.$$
    fi
  done
  rm -f /tmp/lv_hits.$$ || true
}

for file in "${FILTERED_FILES[@]}"; do
  scan_file "$file"
done

if [[ $had_findings -eq 1 ]]; then
  echo ""
  echo "Blocking push. If this is intentional, sanitize or use placeholders."
  echo "Tip: Export STRICT_PREPUSH=1 to scan all tracked files."
  exit 1
fi

echo "[pre-push] Credential scan passed for ${#FILTERED_FILES[@]} files."
exit 0

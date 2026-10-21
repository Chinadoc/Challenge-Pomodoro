# Credential cleanup, 2026-10-21

Remove the committed .env, replace credential examples with blank placeholders, and ignore local environment files. Deletion does not erase Git history or rotate credentials. Previously exposed API credentials require provider-side revocation; do not copy them back from history.

Validation: credential placeholders are empty, and .env is absent from the proposed tree. A fresh Python dependency resolution was audited with zero known vulnerabilities. A syntax scan found three existing, unchanged errors in pomodoro_enhanced/ui/main_window.py, pomodoro_enhanced/ui/task_panel.py and pomodoro_enhanced/core/resources.py. This credential-only change does not repair those existing application defects. No provider requests, GUI launch or paid API calls were made.

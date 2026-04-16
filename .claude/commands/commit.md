# Commit Changes

## Steps
1. **Sync**: Pull the latest changes from the remote.
2. **Stage**: Identify and stage a group of files representing a single logical change.
3. **Draft Message**: Generate a concise, descriptive commit message following conventional commit standards.
4. **Attempt Commit**: Run `git commit -m "[message]"`.
5. **Handle Errors**: If the commit fails (specifically due to pre-commit hooks or linting):
   - Read `.claude/skills/lint-error-fixer.md`.
   - Apply fixes to the staged files.
   - Re-stage and attempt the commit again.
6. **Push**: Push the successful commit to the remote.

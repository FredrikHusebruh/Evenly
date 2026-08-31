# Tooling & workflow

- Python dependencies are managed with `uv` (`uv add` / `uv sync`); run tooling through `uv run`. This includes tests — see [testing.md](testing.md).
- Run the project's linter and type-check/build before treating work as done — type errors surfacing in the build count as failures.
- Style with Tailwind utility classes; avoid adding new CSS files or inline `style=` unless the value is genuinely dynamic.
- Import TypeScript types with `import type { ... }` rather than plain imports.

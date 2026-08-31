# Engineering principles

- **Single responsibility.** One module/component/function per concern. If something does more than one thing, split it. In React: if a component's JSX and its state logic are both growing, pull the state logic into a custom hook. In an API: one router per resource, one service per domain concern.
- **Composition over inheritance.** Wire behavior together through function/class composition and dependency injection (e.g. FastAPI `Depends()`, React children/hooks) — never deep class hierarchies.
- **Fail loudly and early.** Validate at the boundary and raise an explicit, typed error the moment something is invalid. Never swallow an exception with a bare `except`, silently return `None`/an empty value to mean "something went wrong," or render a silent fallback that hides a bug.
- **Never trust data crossing a boundary.** Validate/narrow all external input (API responses, form input, request bodies) before using it. Re-check authorization server-side on every request — never trust a client-supplied ID, role, or ownership claim. See [security.md](security.md) for the boundary-validation and authorization rules this implies.
- **Treat data as immutable.** Functions that transform data return new objects; never mutate schemas, models, state, or props in place. Derive new values instead of editing existing ones.
- **Document the "why," not the "what."** Every exported/public component, hook, service, and non-trivial function gets a short doc comment describing its purpose and any non-obvious constraint. Skip comments that restate the code. Give API route decorators a `summary`/`description` so generated OpenAPI docs stay meaningful.
- **Prefer small, reusable, cohesive modules** over one-off logic duplicated across call sites. A well-named shared helper scales better than the same logic copy-pasted into multiple places.
- **Delete unused code** instead of silencing the compiler/linter (no `_`-prefixing to dodge unused-variable checks).

See also: [architecture.md](architecture.md) for how these principles map onto layered structure.

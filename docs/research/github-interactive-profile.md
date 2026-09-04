# GitHub interactive profile: official constraints and architecture

Research date: 2026-09-04. Sources: GitHub documentation and GitHub-owned repositories only.

## Hard boundary: profile README

- Profile README is rendered from root `README.md` in public repository named exactly like account. [GitHub Docs](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)
- GitHub sanitizes rendered markup. `script` tags, inline styles, `class`, and `id` attributes are aggressively removed. Therefore README cannot run custom JavaScript, attach touch handlers, maintain client state, or provide true filters/tooltips/drill-down controls. [GitHub-owned `github/markup`](https://github.com/github/markup)
- README can still use native links, images, animated GIF/SVG assets accepted by renderer, and HTML disclosure elements GitHub permits. Treat these as navigation or limited native disclosure, not application interactivity.

## Correct solution

- Keep README as fast visual launch surface: compact live snapshot image, clear CTA, links into full dashboard.
- Put real touch-sensitive UI on GitHub Pages. Pages serves repository HTML, CSS, and JavaScript, so responsive controls, pointer/touch input, tabs, filters, tooltips, drill-downs, charts, local state, and accessible keyboard behavior are viable. It remains static hosting; no PHP, Ruby, Python, or other server-side runtime. [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) [Creating a Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- Recommended data pattern: GitHub Actions periodically fetches/aggregates telemetry using server-side `GITHUB_TOKEN`, writes sanitized static JSON and/or SVG, then deploys Pages. Browser consumes generated JSON. Secrets never enter bundle.
- Optional browser refresh: GitHub REST API supports CORS from any origin. Use only public endpoints without embedded credentials; show cached build data when request fails. [GitHub CORS documentation](https://docs.github.com/en/rest/using-the-rest-api/using-cors-and-jsonp-to-make-cross-origin-requests)

## API constraints

- Unauthenticated REST: 60 requests/hour, associated with originating IP. Authenticated user: normally 5,000 requests/hour. Actions `GITHUB_TOKEN`: 1,000 requests/hour per repository. [REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- Browser token is unsafe: authentication requires token in `Authorization`; GitHub explicitly says client secrets must never appear in client-side code or user devices. Same security principle applies to long-lived personal tokens. [REST authentication](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api) [REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- Read rate-limit headers (`x-ratelimit-limit`, `remaining`, `reset`); handle `403`/`429`, `retry-after`, and exponential backoff. Secondary limits include max 100 concurrent requests and generally 900 REST points/minute. [REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- Avoid frequent polling. Request minimal stable payloads. GitHub recommends webhooks over polling and authenticated conditional requests using `ETag`; a valid authenticated `304` does not count against primary limit. Static Pages cannot receive webhooks, so scheduled Action generation is safer than every visitor polling GitHub. [REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)
- GraphQL requires authentication and uses point-based limits (normally 5,000 points/hour for users; 1,000 points/hour/repository for Actions `GITHUB_TOKEN`). Keep GraphQL inside Action, never anonymous browser path. [GraphQL limits](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api)

## Pages deployment

- Select GitHub Actions as Pages source. Workflow: trigger on default-branch push (plus optional schedule/manual run), checkout, build static files, upload via `actions/upload-pages-artifact`, deploy via `actions/deploy-pages`. GitHub recommends `github-pages` environment and protection limiting deployment to default branch. [Publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- Pages limits relevant here: 1 GB published-site max, 10-minute deployment timeout, soft 100 GB/month bandwidth. Soft 10 builds/hour does not apply to custom Actions publishing. [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)

## Product implications

1. “Everything interactive inside GitHub profile README” is technically impossible under GitHub sanitization.
2. “Interactive from profile” is viable: README snapshot links to full Pages dashboard.
3. Make controls at least 44x44 CSS px, use Pointer Events for mouse/pen/touch, never rely on hover alone, include visible focus and `prefers-reduced-motion` handling.
4. Build-time telemetry should be canonical. Optional live public REST refresh should be sparse, cached, cancellable, and nonessential.
5. Label freshness (`Updated …`) and surface graceful stale/offline state.


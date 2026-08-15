# Engineering Notes

## GitHub is the evidence surface

Agent Forge already has a website and an interactive tour. Recreating either inside this repository would split the brand, duplicate maintenance, and suggest a second product implementation.

The repository therefore uses GitHub for what GitHub does best:

- durable architecture and codebase documentation;
- inspectable change history and pull-request review;
- automated public-boundary, link, build, and security checks;
- issues, discussions, projects, releases, and dependency maintenance;
- authentic screenshots that link reviewers to the canonical product.

## Evidence types

Public claims are supported by one of four evidence types:

1. an already-public website or tour surface;
2. a read-only, point-in-time inventory of the private repository;
3. an inspectable file or workflow in this public repository;
4. an explicitly labeled architectural description that withholds implementation policy.

## Why source is not partially copied

Production modules depend on private configuration, prompts, provider integrations, persistence, authentication, and operational context. Publishing isolated files would create a misleading code sample while increasing disclosure risk. Responsibility maps and verified repository counts give reviewers useful engineering signal without presenting fragments as a runnable product.

## Why the repository does not deploy a website

Repository metadata, README links, and screenshots send reviewers to the canonical website and existing tour. CI packages the engineering dossier as a release artifact; it does not deploy another landing page. This preserves one brand, one public product URL, and one tour.

## Why screenshots are committed

Recruiters should be able to understand the product directly from the README. Captures are taken only from public, unauthenticated surfaces and visually reviewed before commit. They are evidence of the existing product—not replacement mockups.

## Why publication has its own CI gate

Passing application tests does not prove a repository is safe to publish. The dedicated boundary scanner examines paths, text, binary allowlists, credential patterns, local endpoints, and accidental API wiring. Human review remains mandatory because context and screenshots cannot be judged reliably by pattern matching alone.

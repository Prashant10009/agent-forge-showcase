# Brand Identity

The public repository follows the established Agent Forge identity. It does not introduce a portfolio-only visual system.

## Core idea

**Fire meets machine.**

The forge is a tool of transformation: heat, pressure, and intention turn raw material into something precise. The triangular mark is both an **A** for Agent and a flame in motion. Its crossbar is the workbench. Rotation is the breath of a system that is always running hot.

The visual character is dark, industrial, sharp, alive, and controlled. The public website can be cinematic; the product workspace remains operational and dense.

## Canonical palette

| Role | Value | Use |
|---|---|---|
| Brand fire | `#ff4500` | Primary identity, selected state, and logo energy |
| Hot flame | `#ff6600` | Highlights and active fire motion |
| Active flame | `#ff2200` | Animated logo color cycle |
| Ember | `#cc1100` | Deeper fire motion and secondary brand energy |
| Void | `#070709` | Primary dark environment |
| Elevated surfaces | `#0d0d12` through `#1e1e28` | Product workspace depth |
| Primary text | `#e2dede` | Headings and critical information |
| Secondary text | `#9a9ab0` | Explanatory copy and metadata |

Brand fire is not a universal status color. Success, warning, information, and failure retain separate semantic colors so operational meaning stays legible.

## Typography

The identity has two related expressions:

- **Public website:** cinematic display type, editorial body copy, and mono technical labels.
- **Product workspace and brand documentation:** Syne for product display and Space Mono for operational metadata.
- **Portable SVG exports:** a system sans-serif stack so downloaded wordmarks remain self-contained without remote font requests.

The split is intentional: the website creates entry and emotion; the application optimizes dense system comprehension.

## Mark and lockups

The authoritative mark uses this fixed geometry:

```text
viewBox: 0 0 88 76
path: M44,8 L84,76 L68,76 L68,65 L20,65 L20,76 L4,76 Z M20,60 L68,60 L68,57 L20,57 Z
fill rule: evenodd
```

The public [logo asset index](../assets/brand/README.md) provides every documented SVG sample:

- primary stacked lockup;
- horizontal lockups for dark and light contexts;
- animated marks at 16, 24, 36, and 52 pixels;
- static, thinking-state, topbar, watermark, and monochrome variants.

The primary documentation/header asset is [`agent-forge-primary-stacked.svg`](../assets/brand/agent-forge-primary-stacked.svg). Preserve the mark geometry, proportions, clear space, and fire palette. Do not substitute unrelated geometric marks.

## Motion

- Product-capable marks rotate on a `3s linear infinite` cycle.
- The fire color moves through `#ff2200`, `#ff6600`, `#ff4500`, and `#cc1100` on a `2.4s ease-in-out infinite alternate` cycle.
- Reduced-motion preferences use the static `#ff4500` fallback.
- Static variants are reserved for print, PDF, email, merchandise, or other environments where animation is unavailable.
- Motion communicates identity or state; it is not decoration applied to every surface.

## Repository application

GitHub is the engineering-documentation surface. The README uses the primary stacked lockup, authentic public website and tour captures, and technical architecture diagrams. Repository links point to the existing website instead of presenting a second branded product.

The previous standalone SVG was removed because it came from a stale brand export and is not part of the current logo system.

---
name: design-audit
description: Use when a UI component, page or stylesheet has just been built or changed and its visual quality needs checking, when the user asks whether a screen looks right, consistent or polished, or before shipping front-end work.
---

# Design Audit

Judge the rendered screen, not the code. Measure against the project's own design system first and general principles second. This skill audits how the interface looks; `ux-audit` covers how it works.

## Evidence first

1. Open the page with a browser tool. Capture it at 375, 768 and 1280 wide, in light and dark if both exist.
2. Trigger each state: hover, focus, active, disabled, loading, empty, error, long text.
3. No way to render it: audit from code, and say so at the top of the report.

## Order of authority

1. The repo's design system: `DESIGN.md`, tokens, Tailwind theme, CSS variables, component library.
2. Neighbouring screens in the same product.
3. The principles below.

## Checklist

| Area | Ask |
|---|---|
| Hierarchy | Is there one primary action per view? Blur the screenshot: does the eye land on the right thing first? |
| Spacing | Is every gap a value from the scale? Are related items closer together than unrelated ones? |
| Typography | Sizes and weights from the type scale? Body line length 45 to 75 characters? At most two families? |
| Colour | Tokens, not raw hex? Text contrast at least 4.5:1, large text and UI parts 3:1? Is anything shown by colour alone? |
| Alignment | Do edges line up on a shared grid? Any element off by a few pixels? |
| Consistency | Same component, same look everywhere? One radius set, one shadow set, one icon family and stroke? |
| States | Does every interactive element have hover, visible focus, active, disabled and loading? |
| Responsive | No horizontal scroll at 375? Touch targets at least 24px, 44px where it matters? Does content reflow instead of shrinking? |
| Dark mode | Any hard-coded colour, invisible border or glaring image? |
| Motion | Does each animation explain a change? 150 to 300ms? Honours `prefers-reduced-motion`? |
| Media | Images with fixed aspect ratio, so nothing jumps on load? |
| Density | Too cramped to scan, or so airy that one task needs scrolling? |

## Severity

- **Broken:** unreadable, overlapping, clipped, or unusable at a supported size.
- **Inconsistent:** departs from the design system or neighbouring screens.
- **Polish:** would look better. At most five.

## Every finding

```
<screen or component> (<file>:<line>) [SEVERITY]
Seen: <what is there, with measured values: "gap 18px", "contrast 3.1:1">
Rule: <token, system rule or principle broken>
Fix: <the exact value or class to use>
```

## Output

```markdown
## Verdict: SHIP | FIX FIRST
Checked: <pages, widths, themes, states> | Evidence: rendered | code only
Top three fixes: <one line each>

### Broken
### Inconsistent
### Polish
### Not checked
```

## Rules

- Report findings; change code only when asked.
- Every finding carries a measured value and a named rule. Taste with no rule is labelled `opinion` and filed under Polish.
- Do not propose a redesign. A new visual direction is a separate request.

# Diagram and presentation integrity

Load for workflow diagrams or reuse of existing presentation definitions. Map
the authoritative editable diagram, renderer/configuration, manifest and generated
assets before editing. Preserve source/asset provenance; do not make generated
SVG the sole source of a maintained diagram.

## Semantic source contract

Record stable nodes, labels, directed edges, decision outcomes, loops and
optional/proposed connection types from the approved source. Preserve their
meaning across wide, narrow, staged and print representations. Simplifying a
diagram is not permission to remove a decision, a return-to-review loop or a
qualification such as proposed versus demonstrated.

- Each decision retains all mapped outcomes and destinations, including unknown
  or unresolved branches when present. Preserve edge labels, not just node names.
- Keep feedback loops connected; a stage boundary must identify continuation and
  preserve the full connected pathway or an equivalent text description.
- Optional/proposed edges remain differentiated in both graphics and words. Do
  not turn a dashed proposal into a solid established connection.
- Regenerate with the mapped existing renderer, then compare full source,
  configuration and generated-asset hashes against the manifest for that build.
  An authorized source edit needs newly generated matching assets, not a stale
  manifest assertion. Missing renderer/dependencies blocks regeneration.

Treat identity and semantics as separate checks: a matching SVG hash says which
asset was used, not whether a decision was lost during the intended source edit.
Verify semantic requirements against an independently retained contract, not one
silently regenerated from an already damaged diagram.

## Static self-contained SVG allowlist

Use a fail-closed element/attribute allowlist tailored to the mapped renderer.
Permit only required static geometry/text/definition elements and approved
presentation attributes. For example, `svg`, `g`, `defs`, `path`, `rect`, `circle`,
`line`, `polyline`, `polygon`, `text`, `tspan`, `title`, `desc`, `marker` and
`clipPath` may be needed; this list is illustrative, not automatic approval for
every renderer output. Unknown tags, namespace tricks or attributes fail closed.

Reject scripts, event-handler attributes, executable links, animation, `set`,
`foreignObject`, frames, embedded objects/images, external references/resources,
XML document-type/entity declarations and processing instructions. Reject
`javascript:`, remote/file/data URLs, external `href`/`src`, CSS `@import` and
nonfragment CSS `url(...)`. Embedded CSS, if required, needs its own restricted
grammar/allowlist; never trust an arbitrary stylesheet because it is inline.
Do not silently strip unsafe content and claim the original diagram is preserved.

Allow a fragment reference only to a defined approved internal element. Validate
syntax before identifier rewriting and references afterward. A static diagram
does not require interactive SVG links; report navigation can stay in checked
surrounding HTML.

## Identifier namespace and references

Assign each embedded diagram/layout instance a distinct stable prefix. Reject
duplicate original IDs; build an exact old-to-new map and rewrite IDs and every
supported internal reference together: fragment `href`/`xlink:href`, `url(#id)`
in approved attributes/styles, clip/marker/gradient references, and token lists
in `aria-labelledby`/`aria-describedby`. Avoid substring replacement that corrupts
IDs with shared prefixes. Fail on dangling references and unsupported reference
syntax. Verify uniqueness across the **whole report**, including repeated assets,
figure headings, controls, title and description IDs.

## Accessibility, print and offline checks

Provide a meaningful title and description, image role and working ARIA
references. Supply a readable text equivalent naming nodes, decisions, outcome
destinations, loop return paths and optional/proposed qualifications; a list of
node labels alone is not equivalent to the diagram.

Actually inspect keyboard access/focus to scrollable regions and disclosures,
narrow-layout legibility/overflow, readable print with full semantic content,
restoration after print, and offline requests/console errors. A large minimum
width plus an inaccessible clipped viewport is not a narrow-layout solution.
Hidden text equivalents or missing print stages must not erase decisions.

## Reuse presentation definitions

Read the maintained canonical palette, typography, marker-area/count mapping,
camera/framing and other applicable presentation definitions through the existing
adapter rather than duplicating independent configuration. Record canonical
source hashes and extraction boundaries; fail on an unexpected boundary instead
of falling back to guessed settings. This does not authorize altering or deploying
the canonical viewer or embedding restricted viewer payloads.

An aggregate overview may deliberately fit a different extent from an individual
viewer; document the adaptation and preserve encoding meaning. Marker **area**
may represent count only under its mapped contract. Mixed-group opacity must
not imply individual severity. Reuse does not mean pixel-identical reproduction.

After [profile mapping](report-profile.md), inspect `namespace_svg` and
`verify_diagram` in `research/scripts/report_checks.py` for applicable assistance.
These helpers do not replace renderer identity checks, independent semantic
contracts or actual keyboard/narrow/print/offline inspection. Report each outcome
separately using [rebuilding](rebuilding.md).

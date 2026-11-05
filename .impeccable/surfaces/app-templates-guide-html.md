---
version: 1
slug: "app-templates-guide-html"
primary_target: "app/templates/guide.html"
related_targets: ["app/templates/dashboard.html"]
---

# Surface brief: TV guide and status pages

Scope: `/guide` (primary) and `/` status dashboard, one shared world. Mode: Operate.

Audience and job: a household finds what is on now and tonight from a phone, tablet, laptop or TV browser driven by a remote; a self-hoster checks the cache and configuration. Content is the real lineup and guide data of the tuner. Constraints: no build step, no browser-side CDN, keyboard and remote operable, WCAG 2.2 AA.

Memorable moment: the whole evening reads by colour before a single title is read, and the white now-line shows where the evening stands.

Unresolved: genre coverage depends on the data source (guide.php fills 55% of programmes; the official XMLTV feed fills all of them).

## Direction contract

THESIS: The guide is the broadcaster's palinsesto sheet. Every programme is a slot filled flat with its genre's colour, and now is one white rule across the sheet. It refuses the category default of grey rounded cards on a slate grid with a blue accent.

OWN-WORLD: A night ground on one fixed eight-step neutral ramp, the only tonal tokens. Flat genre fills with white type and no borders, gradients or shadows: News blue, Drama violet, Comedy plum, Movies red, Sports green, Kids amber, Documentary teal, and Other neutral. Missing data is hatched, never blank. A single white now-line carries a white time tag. Corners are square to 4px. Archivo throughout, semi-condensed in the cells, with tabular figures.

STORY: The visitor sees what is on now on every channel and reads genre by colour. They narrow the sheet by genre, find a title through search that jumps to its slot, and read the details in a pane. On a TV they move with the arrow keys and Enter.

FIRST VIEWPORT:
- Top bar: wordmark, Guide and Status navigation, day tabs, search.
- Under it, the genre legend, which works as a filter, then a time ruler.
- Fixed channel plates (number, logo, name) on the left, with the sheet scrolled so the now-line sits just right of them.
- A detail pane on the right at 1280px and wider; on a phone the plates narrow and the pane becomes a bottom sheet.
- Signature move: the genre filter dims every other genre across the whole sheet.

FORM: Palinsesto Sheet, candidate 6 of my seven. seed: 88a27f4024c4a16c

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

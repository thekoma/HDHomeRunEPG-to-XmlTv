---
name: HDHomeRun EPG
description: The broadcaster's palinsesto sheet. Flat genre slots on a night ground, one white now-line.
colors:
  night-0: "#0e1014"
  night-1: "#15181d"
  night-2: "#1c2026"
  night-3: "#262b33"
  night-4: "#3a414c"
  night-5: "#7d8592"
  night-6: "#a9b0ba"
  night-7: "#eef0f3"
  now-white: "#ffffff"
  genre-news: "#2f5bb7"
  genre-drama: "#6a45b8"
  genre-comedy: "#9a3f82"
  genre-movies: "#b23a3a"
  genre-sports: "#22784d"
  genre-kids: "#9b6311"
  genre-documentary: "#16757a"
  genre-other: "#2e343d"
  state-ok: "#5cc98a"
  state-warn: "#e7b04b"
  state-bad: "#f07c7c"
  danger-line: "#7d3a3a"
  danger-text: "#ffb9b9"
  danger-wash: "#3a1c1c"
  logo-tile: "#e9ecef"
typography:
  headline:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.015em"
  title-sm:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.4
  slot-title:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
    fontVariation: "\"wdth\" 87.5"
  label:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.4
  micro:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.4
    fontFeature: "\"tnum\" 1"
  mono:
    fontFamily: "ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  none: "0px"
  inner: "3px"
  base: "4px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1.25rem"
  xl: "2.5rem"
components:
  button:
    backgroundColor: "{colors.night-2}"
    textColor: "{colors.night-7}"
    typography: "{typography.body}"
    rounded: "{rounded.base}"
    padding: "0 0.875rem"
    height: "2.25rem"
  button-hover:
    backgroundColor: "{colors.night-3}"
  button-pressed:
    backgroundColor: "{colors.night-7}"
    textColor: "{colors.night-0}"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.danger-text}"
    rounded: "{rounded.base}"
    height: "2.25rem"
  button-danger-hover:
    backgroundColor: "{colors.danger-wash}"
  field:
    backgroundColor: "{colors.night-0}"
    textColor: "{colors.night-7}"
    rounded: "{rounded.base}"
    padding: "0 0.75rem"
    height: "2.25rem"
  nav-link:
    backgroundColor: "transparent"
    textColor: "{colors.night-6}"
    rounded: "{rounded.base}"
    padding: "0.45rem 0.75rem"
  nav-link-hover:
    backgroundColor: "{colors.night-2}"
    textColor: "{colors.night-7}"
  nav-link-current:
    backgroundColor: "{colors.night-3}"
    textColor: "{colors.night-7}"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.night-6}"
    rounded: "{rounded.base}"
    padding: "0 0.75rem"
    height: "2rem"
  chip-selected:
    backgroundColor: "{colors.genre-news}"
    textColor: "{colors.now-white}"
  slot:
    backgroundColor: "{colors.genre-news}"
    textColor: "{colors.now-white}"
    typography: "{typography.slot-title}"
    rounded: "{rounded.none}"
    padding: "0 0.625rem 0 0.5rem"
  slot-filtered-out:
    backgroundColor: "{colors.night-2}"
    textColor: "{colors.night-6}"
  now-tag:
    backgroundColor: "{colors.now-white}"
    textColor: "{colors.night-0}"
    typography: "{typography.micro}"
    rounded: "2px"
    padding: "0.0625rem 0.375rem"
  channel-plate:
    backgroundColor: "{colors.night-1}"
    textColor: "{colors.night-7}"
    padding: "0 0.75rem 0 0.5rem"
  tag:
    backgroundColor: "{colors.night-3}"
    textColor: "{colors.night-7}"
    typography: "{typography.micro}"
    rounded: "{rounded.inner}"
    padding: "0.125rem 0.5rem"
  detail-pane:
    backgroundColor: "{colors.night-1}"
    textColor: "{colors.night-7}"
    padding: "1.25rem"
    width: "22rem"
---

# Design System: HDHomeRun EPG

## Overview

**Creative North Star: "The Palinsesto Sheet"**

The interface is the broadcaster's schedule sheet, not an app of cards. Every programme is a rectangle filled flat with its genre's colour and sized exactly by its duration, laid on a night ground of eight neutral steps. The evening reads by colour before a single title is read, and one white vertical rule shows where the evening stands now. Everything that is not the schedule (top bar, legend, ruler, channel plates, the status page) is built from the same neutral ramp and stays quiet so the fills carry the screen.

Density is high and deliberate: rows are 4.25rem, the minute is the only horizontal unit, and labels are semi-condensed Archivo with tabular figures. Depth comes from tone steps and 1px rules, not from lifted surfaces. The same world scales from a phone to a TV browser driven by a remote; on TV the whole interface grows from a 15px to a 24px root, and every control stays reachable with arrow keys and Enter.

The rejected default is the category look: grey rounded cards on a slate grid with a blue accent.

**Key Characteristics:**
- One fixed eight-step neutral ramp is the only tonal scale.
- Flat genre fills with white type; no borders, gradients or shadows on slots.
- One white now-line with a white time tag; white is reserved for now, selection and focus.
- Missing data is hatched, never blank.
- Square to 4px corners.
- Archivo throughout, semi-condensed in the cells, tabular figures for every time and number.

## Colors

A night ground of cool near-blacks, eight saturated-but-deep genre fills that each hold white type at 4.5:1 or better, and pure white used as a signal rather than as a surface.

### Primary
- **Now White** (`now-white`): the now-line, the now tag, the selected-slot inset ring, the focus outline, the selected chip's swatch and all type on genre fills. It is never a background area larger than a tag.

### Secondary: the genre fills
- **Bulletin Blue** (`genre-news`): News. Also the text-selection colour.
- **Drama Violet** (`genre-drama`): Drama.
- **Late Plum** (`genre-comedy`): Comedy.
- **Marquee Red** (`genre-movies`): Movies.
- **Pitch Green** (`genre-sports`): Sports.
- **Saturday Amber** (`genre-kids`): Kids.
- **Deep Teal** (`genre-documentary`): Documentary.
- **Unfiled Slate** (`genre-other`): Other and unclassified programmes; deliberately sits one step above the ground so unclassified time still reads as programmed.

Genre colour reaches a component only through a local fill variable set by the genre class, so slots, legend swatches, chips, tags and search-result swatches always agree.

### Tertiary: service state
- **Online Green** (`state-ok`), **Caution Amber** (`state-warn`), **Fault Rose** (`state-bad`): status dot, inline messages and badges on the status page. Badges use the state colour as text over a 14% wash of itself.
- **Danger set** (`danger-line`, `danger-text`, `danger-wash`): the outline, label and hover wash of the destructive button only.

### Neutral: the night ramp
- **Ground** (`night-0`): page background, field interiors, the 2px gaps between rows and slots.
- **Panel** (`night-1`): top bar, ruler, channel plates, detail pane, table headers, summary cells.
- **Raised** (`night-2`): resting buttons, hover washes, filtered-out slots, logo wells, hatch stripes.
- **Rule** (`night-3`): 1px dividers, hour ticks, pressed nav, neutral tags, button hover.
- **Edge** (`night-4`): control borders, scrollbar thumb.
- **Faint** (`night-5`): placeholders, field hover border, idle status dot.
- **Secondary text** (`night-6`): meta text, inactive nav, tick labels, channel numbers.
- **Primary text** (`night-7`): body text and the pressed-button fill.
- **Logo Tile** (`logo-tile`): a light tile placed behind a channel logo only when the logo is dark on transparency (decided per logo at runtime).

### Named Rules
**The One Ramp Rule.** Every non-genre surface, border and text colour comes from the eight night steps. A new grey is a defect.

**The White Means Now Rule.** Pure white marks now, the current selection and keyboard focus. It is not decoration and not a brand accent.

**The Recede By Colour Rule.** Ended and filtered-out slots lose colour (mixed 45% toward the panel step, or dropped to the raised step), never contrast; their type stays legible.

## Typography

**Display Font:** Archivo (self-hosted variable, weight 100-900, width 62-125%), with ui-sans-serif, system-ui fallback
**Body Font:** Archivo
**Label/Mono Font:** ui-monospace, SF Mono, Menlo for configuration names and values only

**Character:** One grotesque family doing everything, tightened with negative tracking at headline sizes and narrowed to 87.5% width inside programme cells so more of each title fits the minute scale.

### Hierarchy
- **Headline** (700, 1.75rem, -0.015em): page title on the status page.
- **Title** (700, 1.5rem, 1.15, -0.015em, balanced wrap): programme title in the detail pane.
- **Title small** (700, 1.125rem): wordmark and section headings.
- **Body** (400, 15px root, 1.4; descriptions at 1.55 and max 65ch): running text, nav, buttons (600 on buttons, 500 on nav and chips).
- **Slot title** (600, 0.875rem, width 87.5%): programme names in the sheet; single line with ellipsis.
- **Label** (600, 0.8125rem): ruler day, table headers, summary terms.
- **Micro** (600, 0.75rem, tabular): tick times, slot times, tags, badges, now tag.

### Named Rules
**The Tabular Clock Rule.** Every time and number uses tabular figures so columns of times align down the sheet and tables.

**The Root Scale Rule.** Sizes are in rem off a 15px root so the TV root of 24px scales the whole interface at once. Do not set type in px.

## Layout

The guide is a full-viewport column: top bar, genre legend, then a workspace that holds the sheet and, at 1280px and wider, a 22rem detail pane on the right. Only the sheet scrolls, in both axes.

The sheet has one horizontal unit, the width of a minute (0.4rem; 0.3rem on phones). A slot's left edge and width are its start and duration multiplied by that unit; ticks, the midnight rule and the now-line use the same multiplication. Channel plates (15rem; 6.5rem on phones) stick to the left, the time ruler (2rem) sticks to the top, and slot labels stick just right of the plates so a long programme keeps its title in view. Rows are 4.25rem (3.75rem on phones) and are separated by a 2px gap of ground colour; slots are separated by a 2px inset of the same.

Breakpoints: at 1279px and below the detail pane becomes a bottom sheet (max 75dvh) that slides up; at 767px and below the status summary drops from four columns to two; at 639px and below the top bar tools take a full row, the search field stretches, the legend fades at its right edge to show it scrolls, and plates stack logo over name without the channel number. TV browsers get a 24px root.

The status page is a centred column (max 72rem, 2rem 1.25rem 4rem padding) with sections spaced 2.5rem apart. Spacing otherwise moves in small steps of 0.25, 0.5, 0.75 and 1.25rem.

## Elevation & Depth

The system is flat. Depth is carried by tone steps of the night ramp (ground, panel, raised) and 1px rule lines. Slots, plates, tables and buttons never cast shadows. The only shadows belong to the two surfaces that genuinely float above the sheet, and both are soft, dark and ambient.

### Shadow Vocabulary
- **Popover** (`box-shadow: 0 12px 32px rgb(0 0 0 / 0.5)`): the search results list.
- **Bottom sheet** (`box-shadow: 0 -16px 40px rgb(0 0 0 / 0.55)`): the detail pane when it rises from the bottom below 1280px.

### Named Rules
**The Only Floaters Cast Rule.** A shadow is allowed only on a surface that overlays the sheet. Anything in the layout flow is flat.

## Shapes

Square to 4px. Programme slots are hard rectangles (0 radius) because they are measurements of time. Controls, panels and tables use a 4px corner; small inner elements (logo wells, tags, badges, pane image) use 3px; the now tag uses 2px. The status dot is the one circle. Missing data is drawn as a 135-degree hatch of panel and raised stripes (0.375rem and 0.125rem), on empty lanes and on channels without a logo.

## Components

### Buttons
Quiet, bordered, and the same height as fields so they sit in one row.
- **Shape:** gentle 4px corner, 2.25rem tall (day tabs 2rem).
- **Default:** raised fill, edge-step border, primary text, weight 600.
- **Hover / Focus:** fill steps up to the rule step; focus is the global 3px white outline offset 2px.
- **Pressed (toggle):** inverts to primary-text fill with ground-colour type; used for the selected day.
- **Danger:** transparent with a dark red outline and rose label, a dark red wash on hover; reserved for destructive cache actions.
- **Disabled:** 50% opacity, not-allowed cursor.

### Chips (genre legend)
- **Style:** transparent, secondary text, a 0.75rem square swatch of the genre fill before the label.
- **State:** hover lifts to the raised step; selected fills the whole chip with its genre colour, white type, and a white swatch. Selecting a chip is the filter.

### Inputs / Fields
- **Style:** ground-colour interior, edge-step border, 4px corner, 2.25rem tall.
- **Focus:** border turns white and the white outline sits flush (offset 0). Hover lifts the border to the faint step.

### Navigation
Wordmark, then Guide, Status and API as text links in the top bar. Inactive links are secondary text; hover gets the raised wash; the current page holds the rule-step fill. On phones the bar wraps and the tools take their own row.

### Programme Slot (signature)
A flat rectangle of genre fill with white semi-condensed title and tabular time, sized by duration. Hover brightens it 15%. Selected gets a 2px white inset ring; focus a 3px white outline inset. Short programmes hide their text visually and keep it for screen readers; an airing slot pushes its label past the now-line. Ended slots recede by colour mix. Arrow keys move along the lane and between channels at the same time, like a remote.

### Genre Filter (signature)
Selecting a legend chip drops every slot to the raised step with secondary text, except the chosen genres, which keep their fill. The whole evening dims except what was asked for.

### Now-line and Now Tag
A 2px white vertical rule through every lane at the current minute, with a white tag carrying the time in the ruler. Midnight is a fainter 1px rule at 45% white with a 2px tick in the ruler.

### Channel Plate
Sticky left column on the panel step: tabular channel number, logo in a 2.25rem well (hatched when missing, light tile when the logo is dark), name in 600 with ellipsis.

### Detail Pane
Panel-step column with a 4:3 image, balanced title, when and channel lines, tags (neutral, or genre-filled for the genre), the description at 65ch, and a "next on" line under a rule. Becomes a sliding bottom sheet with a Close button below 1280px.

### Status Summary and Tables
Summary is a grid of panel cells separated by 1px rule-step gaps inside a 4px frame. Tables have sticky panel-step headers in label type, 1px raised-step row lines, a panel-step hover, monospace for configuration names and values, and state badges at 3px.

## Do's and Don'ts

### Do:
- **Do** take every neutral from the eight night steps (`night-0` to `night-7`).
- **Do** give every genre surface its colour through the genre class and its fill variable, with white type.
- **Do** size anything on the sheet in minutes multiplied by the one time unit.
- **Do** hatch missing data with the 135-degree panel and raised stripes.
- **Do** use tabular figures for all times and counts.
- **Do** keep every interactive element reachable by Tab and arrow keys, with the 3px white focus outline.
- **Do** set sizes in rem so the 24px TV root scales the interface.

### Don't:
- **Don't** put borders, gradients, rounded corners or shadows on programme slots.
- **Don't** use white as a fill or decorative accent; it means now, selection or focus.
- **Don't** dim ended or filtered slots by lowering text contrast; remove colour instead.
- **Don't** introduce a radius above 4px or a new grey outside the ramp.
- **Don't** add shadows to anything that does not float over the sheet.
- **Don't** fall back to grey rounded cards on a slate grid with a blue accent.

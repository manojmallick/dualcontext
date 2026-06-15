---
name: DualContext
colors:
  surface: '#0e150e'
  surface-dim: '#0e150e'
  surface-bright: '#343b33'
  surface-container-lowest: '#091009'
  surface-container-low: '#171d16'
  surface-container: '#1b211a'
  surface-container-high: '#252c24'
  surface-container-highest: '#30372e'
  on-surface: '#dde5d8'
  on-surface-variant: '#bdcab9'
  inverse-surface: '#dde5d8'
  inverse-on-surface: '#2b322a'
  outline: '#879484'
  outline-variant: '#3e4a3c'
  surface-tint: '#64df74'
  primary: '#82fd8e'
  on-primary: '#003910'
  primary-container: '#65e075'
  on-primary-container: '#006120'
  inverse-primary: '#006e26'
  secondary: '#68dbae'
  on-secondary: '#003827'
  secondary-container: '#26a37a'
  on-secondary-container: '#003121'
  tertiary: '#ffdccd'
  on-tertiary: '#50240b'
  tertiary-container: '#ffb794'
  on-tertiary-container: '#7a462a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#81fc8d'
  primary-fixed-dim: '#64df74'
  on-primary-fixed: '#002106'
  on-primary-fixed-variant: '#00531a'
  secondary-fixed: '#86f8c9'
  secondary-fixed-dim: '#68dbae'
  on-secondary-fixed: '#002115'
  on-secondary-fixed-variant: '#00513a'
  tertiary-fixed: '#ffdbcb'
  tertiary-fixed-dim: '#feb693'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#6b3a1f'
  background: '#0e150e'
  on-background: '#dde5d8'
  surface-variant: '#30372e'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin: 24px
---

## Brand & Style
The design system is engineered for high-performance developer environments where precision and data density are paramount. The aesthetic is a hybrid of **Minimalism** and **Technical Modernism**, prioritizing legibility and functional hierarchy over decorative elements. 

The UI should evoke a sense of "command and control"—a focused, low-distraction environment that feels industrial yet refined. By utilizing deep obsidian surfaces and vibrant technical accents, this design system creates a high-contrast workspace that reduces eye strain during long debugging or monitoring sessions. The visual language uses sharp definition, thin lines, and purposeful color application to guide the user through complex information architectures.

## Colors
The palette is built on a "Dark Slate" foundation to maximize contrast for data visualization. 
- **Operational Green (#65E075):** Reserved for active status, successful queries, and live streaming data.
- **Context Teal (#1D9E75):** Used for structural code elements, navigation highlights, and secondary technical identifiers.
- **The Gradient:** Utilized exclusively for primary "Call to Action" elements or signifying the bridge between operational data and code context.
- **Surface Strategy:** Use `#0B0D12` for the main application shell. Elevate functional zones using `#151820` and use `#1C2030` for floating panels or interactive cards to create a clear z-axis hierarchy.

## Typography
Typography is split between **Inter** for all interface controls and **JetBrains Mono** for technical content. 
- Use `headline-lg` sparingly for main dashboard titles.
- `code-md` and `code-sm` are the workhorses for log streams and SPL editors; ensure line-height remains consistent to maintain the vertical rhythm of code.
- `label-caps` should be used for table headers and small metadata labels to differentiate them from interactive body text.
- Maintain a tight letter-spacing on headlines to reinforce the high-tech, precise feel.

## Layout & Spacing
The design system utilizes a **Fluid Grid** with a 4px baseline unit to ensure high density without visual clutter.
- **Density:** Favor "Compact" spacing for data tables and logs (8px padding). Use "Standard" spacing (16px padding) for forms and settings.
- **Desktop:** 12-column grid with 16px gutters. Sidebars should be fixed at 240px or 280px depending on the complexity of the navigation tree.
- **Tablet/Mobile:** Reflow to a single column. Information density should be scaled back—hide non-essential metadata in a "Details" chevron rather than overflowing horizontally.

## Elevation & Depth
In this dark-mode-first system, depth is communicated through **Tonal Layering** and **Subtle Outlines** rather than heavy shadows.
- **Level 0 (Background):** `#0B0D12` - The base canvas.
- **Level 1 (Surface):** `#151820` - Used for primary content containers.
- **Level 2 (Overlay):** `#1C2030` - Used for modals, dropdowns, and cards.
- **Borders:** Every container must have a 1px solid border of `#2A3347`. This "ghost border" technique provides the necessary definition against the dark background.
- **Interactions:** On hover, borders should brighten to `#9CA3AF` or the Primary Green to indicate focus.

## Shapes
This design system uses a **Soft (Level 1)** roundedness profile to maintain a professional, engineered look.
- **Standard Elements:** 4px (0.25rem) radius for input fields, buttons, and small containers.
- **Large Containers:** 8px (0.5rem) radius for cards and main content areas.
- **Badges/Pills:** Full "pill" rounding (999px) to distinguish them from interactive buttons.
- **Tabs:** Use sharp corners for the bottom of active tabs to reinforce their connection to the content pane below.

## Components
- **Buttons:** 
    - *Primary:* Gradient background (`accent_gradient`) with black text for maximum contrast.
    - *Secondary:* Transparent with a `#2A3347` border and white text.
    - *Tertiary:* Ghost style (no border/background until hover).
- **Badges:** 
    - Use a pill shape with a subtle background tint of the status color (e.g., 10% opacity Green) and a solid 6px status dot positioned to the left of the text.
- **Cards:** 
    - Background: `#1C2030`. Border: 1px `#2A3347`. Use no shadows; let the tonal difference create the separation.
- **Input Fields:** 
    - Background: `#0B0D12`. Border: 1px `#2A3347`. Focus state: Border becomes `#65E075` with a subtle 2px outer glow.
- **Code Blocks:** 
    - Inset background of `#050505` (pure black) to create a "well" effect. Line numbers should be rendered in `#9CA3AF`.
- **Charts:**
    - Use sharp 1px or 2px lines. Avoid area fills unless they are low-opacity (0.1) gradients. Use the Brand Green for the primary data series and Teal for the secondary.
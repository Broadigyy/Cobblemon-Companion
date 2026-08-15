# Cobblemon Companion v1.8.2 — Public Tester Release

V1.8.2 combines the new V1.8 collection/team/spawn features with a cleanup and reliability pass driven by tester feedback.

## Highlights

### Collection Expansion
- Living Dex
- Shiny Dex
- Form Dex
- separate completion tracking and filters

### Saved Builds
Save an individual Pokémon build — nature, ability, held item, EVs and moves — and reuse it across teams.

### Team Sharing
Copy/export a full team code and import it into another Cobblemon Companion install.

### Spawn Finder
Spawn Finder can now work in both directions:
- Pokémon → where can it spawn?
- Area/conditions → what can spawn here?

### Dashboard
Home has been renamed **Dashboard** and remains customizable.

### Backup & Restore
Settings can export a portable `.ccbackup` containing Collection, teams, builds, hunts, Bingo, Dashboard preferences and other profile data.

Restore validates backups before replacing profile data and keeps a safety copy of the previous profile.

### Data Audit
Settings now includes a local audit that checks imported Pokémon/forms, move-data completeness, items, competitive held-item fallbacks, and Mega Stone coverage.

## Tester fixes

- Added **Damp Rock**
- Added audited fallbacks for Heat Rock, Icy Rock, Smooth Rock and Terrain Extender
- Removed visible `2.0` page branding
- Removed the abandoned Pokédex screen-scanner experiment

## Testing focus

Please report:

- crashes
- missing Pokémon/forms/items/moves
- incorrect spawn information
- Shiny/Form Dex issues
- Saved Build issues
- team import/export failures
- Backup/Restore issues
- layout/navigation problems
- overlay problems
- modpack compatibility issues

## Windows notice

This build is currently unsigned, so Windows SmartScreen may display an **Unknown Publisher** warning.

Only download Cobblemon Companion from the official repository:

`Broadigyy/Cobblemon-Companion`

# Cobblemon Companion

**Cobblemon Companion** is a free Windows desktop companion for Cobblemon, bringing collection tracking, spawning, competitive tools, overlays, and reference data into one polished application.

> Current public testing version: **v1.8.2**

## Major features

- Pokédex with forms, stats, abilities, learnsets, evolutions, breeding and cross-navigation
- Spawn Finder with Pokémon search and reverse area browsing
- Poké Snack recommendations
- Living Dex, Shiny Dex and Form Dex tracking
- Weekly Bingo
- Hunt Planner
- Competitive Team Builder
- Saved individual Pokémon builds
- Team import/export codes
- Competitive Analysis
- Threat Analyzer
- Team Advisor
- Breeding Planner
- Move / Ability / Item database
- Crafting and cooking recipe views
- Current Hunt overlay
- Weekly Bingo overlay
- Customizable Dashboard
- First-launch onboarding
- Backup & Restore
- Local data completeness audit

## Download

Compiled Windows builds are available from the **Releases** section.

1. Download the latest `Cobblemon_Companion_..._TESTER_RELEASE.zip`.
2. Extract it.
3. Run `Cobblemon Companion.exe`.

Python is not required for the compiled Windows release.

## What's new in v1.8.2

- **Home is now Dashboard**
- Removed visible `2.0` branding from page names
- Added **Damp Rock** and audited additional weather/terrain held-item fallbacks
- Added **Backup & Restore** in Settings
- Added **Run Data Audit** in Settings
- Preserved complete Mega Stone fallback coverage
- The experimental Pokédex screen-scanning branch was intentionally removed

The broader v1.8 feature set also includes Shiny/Form Dex tracking, Saved Builds, Team Import/Export, Spawn Finder reverse browsing, Dashboard customization and onboarding.

## Data storage

Companion stores user profile/cache data separately under:

```text
%APPDATA%\Cobblemon Companion
```

Normal application replacement/updates should not erase Collection, teams, Bingo, hunts, or other profile progress.

## Backup & Restore

Open **Settings → Backup & Restore** to export a `.ccbackup`.

A backup includes profile data such as:

- Living / Shiny / Form Dex
- teams
- saved builds
- hunts
- Bingo
- Dashboard preferences
- profile settings

Restore validates the backup before replacing current profile data and keeps a safety copy of the previous profile.

## Overlays

Current Hunt and Weekly Bingo overlays support:

- always-on-top presentation
- dragging
- resizing
- lock/edit mode
- opacity
- remembered placement

For best results, use Minecraft in **windowed or borderless fullscreen**.

## Support development

Cobblemon Companion is completely free.

☕ **Ko-fi:** https://ko-fi.com/broadigy

No paid features, donation nags, or locked functionality.

## Reporting bugs

Please use GitHub Issues and include:

- Companion version
- Minecraft version
- Cobblemon version
- modpack name if applicable
- what you were doing
- screenshots where useful
- crash log if one exists

Crash logs are normally stored at:

```text
%APPDATA%\Cobblemon Companion\crash.log
```

## Source visibility and usage rights

The source is publicly visible for transparency and auditing.

Public visibility does **not** grant permission to copy, redistribute, rebrand, sell, or publish modified versions of Cobblemon Companion.

See `COPYRIGHT.md`.

## Disclaimer

Cobblemon Companion is an independent community project and is not affiliated with, endorsed by, sponsored by, or officially connected to Cobblemon, Mojang Studios, Microsoft, Nintendo, Game Freak, or The Pokémon Company.

Pokémon and related trademarks belong to their respective owners.

---

Made for the Cobblemon community by **Broadigy**.

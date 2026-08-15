# Cobblemon Companion

**Cobblemon Companion** is a free Windows desktop companion for **Cobblemon** that brings common gameplay tools into one polished application.

> Current public testing version: **v1.7.1**

## What it does

Cobblemon Companion includes:

- **Pokédex 2.0** with forms, stats, abilities, learnsets, evolution information, breeding information, and cross-navigation
- **Spawn Finder** using imported Cobblemon/modpack spawn data
- **Poké Snack recommendations** for lure combinations
- **Weekly Bingo tracking**
- **Hunt Planner 2.0** with Bingo / Collection overlap and shared hunting areas
- **Collection 2.0** Living Dex tracking with generation completion
- **Competitive Team Builder**
- **Competitive Analysis**
- **Threat Analyzer**
- **Team Advisor**
- **Breeding Planner**
- **Move / Ability / Item database**
- **Crafting and cooking recipe presentation**
- **Current Hunt overlay**
- **Weekly Bingo overlay**
- Resizable, draggable, lockable, always-on-top overlays
- Saved overlay position, size, and opacity
- Integrated desktop navigation with Back history

## Download

Compiled Windows builds are distributed through the **Releases** section of this repository.

When a release is available:

1. Open the repository's **Releases** page.
2. Download the latest `Cobblemon_Companion_..._TESTER_RELEASE.zip`.
3. Extract the ZIP.
4. Run `Cobblemon Companion.exe`.

Python is **not required** to run the compiled Windows build.

## First launch

Companion can auto-detect many Cobblemon installations. If needed:

1. Open **Settings**.
2. Select your installed Cobblemon `.jar`.
3. Companion will import the species, forms, spawn data, items, moves, and other supported information it can read from the selected modpack.

Companion keeps its own profile/cache data separately under:

```text
%APPDATA%\Cobblemon Companion
```

It does **not** modify your Cobblemon JAR or Minecraft modpack.

## Overlays

The overlay system currently includes:

- **Current Hunt**
- **Weekly Bingo**

Overlays can be moved, resized, locked, and given adjustable opacity.

For the most reliable behavior, Minecraft should be played in **windowed or borderless fullscreen** mode. True exclusive fullscreen may cover normal Windows top-level overlays.

Use:

```text
Ctrl + Shift + O
```

to jump directly to Overlay controls.

## Screenshots

<img width="2532" height="1217" alt="image" src="https://github.com/user-attachments/assets/2cc1568a-2c52-429d-9a89-633ed8519158" />
<img width="1175" height="753" alt="image" src="https://github.com/user-attachments/assets/44e2f98f-1cc6-467a-bb28-abd9ceb8cb56" />
<img width="1176" height="754" alt="image" src="https://github.com/user-attachments/assets/5ca19590-f380-4368-ab12-52098afad2d1" />
<img width="1322" height="754" alt="image" src="https://github.com/user-attachments/assets/255f2c5a-b291-4a65-aa74-29543854eb2e" />



## Support development

Cobblemon Companion is free.

If you enjoy using it and want to support continued development:

**☕ Ko-fi: https://ko-fi.com/broadigy**

There are no paid features, donation nags, or locked functionality.

## Reporting bugs

Please use the **Issues** tab on GitHub.

When reporting a bug, include:

- Companion version
- Cobblemon version
- Minecraft version
- What you were doing when it happened
- Screenshot if applicable
- `crash.log` if one was created

Crash logs are normally stored in:

```text
%APPDATA%\Cobblemon Companion\crash.log
```

## Source code and usage rights

The source is publicly visible so users can inspect what the application does and so development can be transparent.

**Public visibility does not grant permission to copy, redistribute, rebrand, sell, or publish modified versions of Cobblemon Companion.**

See [COPYRIGHT.md](COPYRIGHT.md) for details.

## Privacy

Cobblemon Companion is a local desktop application. It does not require an account and does not operate its own analytics or tracking service.

Some features may contact third-party public data services when obtaining missing reference data or sprites. See [docs/PRIVACY.md](docs/PRIVACY.md).

## Disclaimer

Cobblemon Companion is an independent community project.

It is **not affiliated with, endorsed by, sponsored by, or officially connected to Cobblemon, Mojang Studios, Microsoft, Nintendo, Game Freak, or The Pokémon Company**.

Pokémon names, characters, images, and related trademarks belong to their respective owners.

Cobblemon belongs to its respective developers and contributors.

---

Made for the Cobblemon community by **Broadigy**.

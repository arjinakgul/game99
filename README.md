# game99

3D oyun geliştirme playground'u. Asset'ler Blender (Python/headless) ile üretilir, oyun Godot 4 ile yapılır.
Detaylı plan: [docs/ROADMAP.md](docs/ROADMAP.md).

## Cloud ortamında hızlı başlangıç

```bash
bash tools/setup_cloud.sh          # Blender + Godot kurar (~10 dk, bir kez)
blender -b --python tools/make_hero_placeholder.py   # karakteri üretir, .glb export + render
cd game-godot && godot --headless --import --path .  # Godot'a import
godot --headless --path . --quit-after 2             # 2 frame çalıştır, "Hero: playing Idle" görmeli
```

GPU olmadığı için Blender EEVEE, Mesa'nın yazılım OpenGL'i (llvmpipe) üzerinde çalışır; render yavaştır
ama önizleme için yeterlidir. Final render için Cycles (CPU) kullanılabilir.

## Mevcut durum
- `assets/characters/hero/hero_placeholder.blend` — blok karakter + 11 kemikli rig + Idle animasyonu
- `assets/exports/hero_placeholder.glb` — Godot'a import edilmiş hali `game-godot/assets/` altında
- `renders/hero_preview.png` — EEVEE önizleme

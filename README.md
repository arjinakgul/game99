# game99

3D oyun geliştirme playground'u. Asset'ler Blender (Python/headless) ile üretilir, oyun Godot 4 ile yapılır.
Detaylı plan: [docs/ROADMAP.md](docs/ROADMAP.md).

## Cloud ortamında hızlı başlangıç

```bash
bash tools/setup_cloud.sh          # Blender + Godot kurar (~10 dk, bir kez)
blender -b --python tools/build_hero.py              # karakter + rig + Idle/Walk, .glb export + render
cd game-godot && godot --headless --import --path .  # Godot'a import
godot --headless --path . --quit-after 2             # 2 frame çalıştır, "Hero: playing Idle" görmeli
```

GPU olmadığı için Blender EEVEE, Mesa'nın yazılım OpenGL'i (llvmpipe) üzerinde çalışır; render yavaştır
ama önizleme için yeterlidir. Final render için Cycles (CPU) kullanılabilir.

## Mevcut durum
- `tools/build_hero.py` → `assets/characters/hero/hero.blend`: stilize low-poly karakter, 19 kemikli
  humanoid rig, Idle + Walk animasyonları
- `assets/exports/hero.glb` → `game-godot/assets/hero.glb` olarak Godot'ta oynatılıyor
- `renders/hero_idle.png`, `renders/hero_walk.png` — EEVEE önizlemeler
- `tools/make_hero_placeholder.py` — pipeline smoke test'i (blok karakter), ortam kontrolü için

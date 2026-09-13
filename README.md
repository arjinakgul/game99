# game99

3D oyun geliştirme playground'u. Asset'ler Blender 5.2 LTS (Python/headless) ile üretilir, oyun Godot 4.7 ile yapılır.
Ana karakter: sokak stili wing chun dövüşçüsü (hoodie, jogger, distopik palet).
Plan: [docs/ROADMAP.md](docs/ROADMAP.md) · Karakter ve animasyon kararları: [docs/CHARACTER.md](docs/CHARACTER.md).

## Cloud ortamında hızlı başlangıç

```bash
bash tools/setup_cloud.sh   # Blender 5.2.1 + Godot 4.7.2 kurar (~10 dk, bir kez)
bash tools/make_all.sh      # karakter build -> mocap retarget -> Godot import + 2 frame test
bash tools/make_all.sh --no-render   # aynısı, kontak sayfası render'ı olmadan (hızlı)

# Godot (kendi makinende): game-godot/ klasörünü Godot 4.7.2 ile aç, F5. WASD hareket, Shift koş, Space zıpla,
# sol tık/J chain punch, sağ tık/K tekme, L blok, F kapüşon (fight mode), Esc fare.
# headless test: (cd game-godot && godot --headless --path . --script smoke_test.gd)  # yürü/koş/zıpla/vur/tekme + düşman canı

# tek tek:
blender -b --python tools/build_hero.py                       # gövde, rig, prosedürel klipler, hero.glb, renders/hero_poses.png
blender -b assets/characters/hero/hero.blend --python tools/retarget_bvh.py -- <bvh>:<Clip> --render
```

GPU olmadığı için Blender EEVEE, Mesa'nın yazılım OpenGL'i (llvmpipe) üzerinde çalışır; render yavaştır
ama önizleme için yeterlidir. Final render için Cycles (CPU) kullanılabilir.

## Mevcut durum
- `tools/build_hero.py` → `assets/characters/hero/hero.blend`: CC0 base mesh parçalarından kurulan stilize wing chun dövüşçüsü, 19 kemikli
  Godot-humanoid rig, prosedürel klipler (Stance, Walk, ChainPunch, FrontKick, BongSau, TanSau, PakSau, Hit)
- `tools/retarget_bvh.py`: BVH mocap → hero rig (Bandai test klipleri: MocapPunch, MocapPunch2, MocapKick)
- `assets/exports/hero.glb` → `game-godot/assets/hero.glb`; Godot Stance klibini döngüde oynatıyor
- `renders/hero_poses.png` — 9 pozluk kontak sayfası (son karesi kapüşon-kapalı varyant)
- `tools/make_hero_placeholder.py` — pipeline smoke test'i (blok karakter), ortam kontrolü için

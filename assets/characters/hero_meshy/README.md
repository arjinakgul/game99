# Meshy ana karakter

Kaynak: Pixellab sprite → Meshy 7 image-to-3D (Pro plan, tam ticari hak).

## Yüklenecek dosyalar (web arayüzünden)
- `hero_meshy_raw.glb`      — remesh edilmiş (~20k üçgen), dokusuz veya dokulu ana model
- `hero_meshy_rigged.glb`   — Meshy auto-rig çıktısı (varsa)
- `hero_meshy_texture.png`  — ayrı doku haritası varsa
- `assets/concept/hero_sprite.png` — kaynak sprite (API ile yeni varyant üretmek için)

## API / MCP
- `.mcp.json` Meshy MCP sunucusunu tanımlar; `MESHY_API_KEY` ortam değişkeni cloud environment ayarlarından verilir.
- `tools/meshy_api.py` aynı işi MCP olmadan REST ile yapar (image2mesh / remesh / rig / download).

## Durum (v1)
- `hero_meshy_v1_mesh.glb`: `assets/concept/hero_concept_v1.png` (Meshy text-to-image, 3 kredi) → Meshy 7 image-to-3D,
  dokusuz, 20k üçgen remesh (20 kredi). Tek parça mesh, A-pozu.
- `tools/rig_meshy.py`: 1,75 m'ye ölçekler, konsept oranlarına göre 19 kemik yerleştirir (chibi oranlar, el ucu
  mesh'ten ölçülür), **mesafe bazlı skinning** (Blender bone heat bu mesh'te başarısız), prosedürel klipler
  (`tools/hero_anims.py`), export `assets/exports/hero_meshy.glb`.
- Mocap klipleri `tools/retarget_bvh.py` ile aynı rig isimleri üzerinden aktarılır (make_all.sh içinde otomatik).
- Web arayüzünde üretilen Pixellab tabanlı model API'den görünmüyor; elle indirilip buraya `hero_meshy_web.glb`
  olarak konursa `rig_meshy.py` ile aynı yoldan işlenir.

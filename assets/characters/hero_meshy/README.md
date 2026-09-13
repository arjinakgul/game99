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

## Durum (v1, Pro ile)
| Dosya | Kaynak | Kredi |
|---|---|---|
| `hero_meshy_v1_mesh.glb` | konsept görsel → Meshy 7 image-to-3D, dokusuz, 20k üçgen | 3 + 20 |
| `hero_meshy_v1_textured.glb` + `_base_color.png` | retexture (düz cel renk prompt'u) | 10 |
| `hero_meshy_v1_meshyrig.glb`, `_meshy_walk.glb`, `_meshy_run.glb` | Meshy auto-rig (24 kemik, Mixamo isimleri) + yürüme/koşma | 5 |
| `hero_meshy_hooddown_v1_mesh.glb` | kapüşon-açık konsept → image-to-3D, dokusuz | 3 + 20 |
| `hero_meshy_hooddown_v1_textured.glb` | retexture | 10 |

Pipeline: `rig_meshy.py --meshy-rig` Meshy iskeletini bizim 19 kemik ismine çevirir (Spine01, ToeBase, head_end vb.
ebeveyne birleştirilir), ağırlıkları dokulu mesh'e nearest-face ile aktarır, prosedürel klipleri kurar;
`retarget_bvh.py` BVH ve GLB (Meshy walk/run) kaynaklarını aynı rig'e aktarır. Sonuç `assets/exports/hero_meshy.glb`,
Godot ana sahnesinde kullanılır. Kapüşon-açık model kendi rig'imizle (mesafe skinning) `hero_meshy_hooddown.glb`.

## Bağlama kalite notları
- Meshy auto-rig ağırlıkları (kapüşon-kapalı model) yakın planda temiz: kapüşon, maske, parmaklar, sargılar.
- Kendi mesafe bağlamamız (kapüşon-açık) chibi kafada kulakları omuz/kol kemiklerine kaptırıyordu (Stance'ta elf kulağı).
  Düzeltme: boyun hizasının üstündeki vertexler yalnızca Head/Neck'e bağlanır; omuzdaki kapüşon kumaşı (arkada, y>0)
  Chest'e sabitlenir. Kol/bacak için ek bölge kuralı DENENDİ ve kaldırıldı: gövde yan vertexlerini kola zorlayıp dev spike
  üretiyordu. Kontrol: `renders/hero_meshy_hooddown_detail.png`, `renders/hero_meshy_detail.png`.
- Yakın plan kontrolü artık standart: her rig değişikliğinden sonra rest / Stance / ChainPunch / FrontKick yakın planı.

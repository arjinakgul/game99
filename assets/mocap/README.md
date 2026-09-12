# Mocap kaynakları

| Klasör | Kaynak | Lisans | Kullanım |
|---|---|---|---|
| `bandai/` | Bandai Namco Research Motiondataset-1 (punch ×2, kick ×1) | CC BY-NC 4.0 | **Sadece retarget pipeline testi.** Yayınlanacak oyunda kullanılamaz. |
| `motifect/` (bekleniyor) | Motifect Martial Arts Motion Pack, itch.io | ticari oyun kullanımı serbest | Oyun içi aday |

Retarget: `blender -b assets/characters/hero/hero.blend --python tools/retarget_bvh.py -- <bvh> <ClipName>`

## Motifect paketini yükleme (kullanıcı)
1. https://motifect.itch.io/motifect-martial-arts-motion-pack → "Download Now" → "No thanks, just take me to the downloads" → `Motifect_martial_arts_v1_0.zip` (~8 MB)
2. Zip'i **açmadan** bu klasöre koy: `assets/mocap/motifect/Motifect_martial_arts_v1_0.zip`
   (Alternatif: GitHub web arayüzünde `assets/mocap/motifect/` içine "Add file → Upload files")
3. `claude/pensive-shannon-k5zd2d` dalına commit + push et (ya da ana dala; ben çekerim)
4. Sonrası bende: zip'i açıp BVH'leri listeler, iskelet isimlerini `NAME_MAPS`'e eklerim, wing chun'a en yakın
   klipleri (yumruk, blok, tekme, duruş) retarget edip kontak sayfasına koyarım.

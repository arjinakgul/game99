# Mocap kaynakları

| Klasör | Kaynak | Lisans | Kullanım |
|---|---|---|---|
| `bandai/` | Bandai Namco Research Motiondataset-1 (punch ×2, kick ×1) | CC BY-NC 4.0 | **Sadece retarget pipeline testi.** Yayınlanacak oyunda kullanılamaz. |
| `motifect/` (bekleniyor) | Motifect Martial Arts Motion Pack, itch.io | ticari oyun kullanımı serbest | Oyun içi aday |

Retarget: `blender -b assets/characters/hero/hero.blend --python tools/retarget_bvh.py -- <bvh> <ClipName>`

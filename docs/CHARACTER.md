# Ana karakter: Sokak stili Wing Chun dövüşçüsü

## Konsept
- Stil: stilize low-poly, flat renk (bkz. ROADMAP)
- Kıyafet: geleneksel değil, sokak stili — hoodie/tişört, jogger/kargo pantolon, spor ayakkabı, bileklik/bandaj
- Duruş: Yee Jee Kim Yeung Ma (içe dönük ayaklar, dizler kapalı), eller centerline'da Wu Sau / Man Sau
- Siluet: kompakt, dirsekler içeride; abartılı kas yok

## Wing Chun animasyon seti (hedef)
| Klip | Teknik | Not |
|---|---|---|
| `Stance` | Yee Jee Kim Yeung Ma + Man Sau/Wu Sau | Idle yerine geçer, hafif nefes |
| `ChainPunch` | Lin Wan Kuen (3 vuruş) | Dikey yumruk, dirsek centerline'da |
| `TanSau` / `BongSau` / `PakSau` | Bloklar | Parry/counter için |
| `LapSau_Punch` | Lap Sau + yumruk | Kombo başlangıcı |
| `FrontKick` | Wing Chun düz tekmesi | Diz yüksekliği, ayak düz |
| `StepAdvance` / `StepRetreat` | Biu Ma / Tui Ma | Kayan adım, gövde dik |
| `Hit` / `KnockDown` | Tepki | Düşman ve oyuncu ortak |

## Animasyon kaynağı araştırması (Eylül 2026)

### A. Hazır mocap paketleri
| Kaynak | İçerik | Format | Lisans | Fiyat |
|---|---|---|---|---|
| Sidekick Animation "Martial Arts – Wing Chun" (Reallusion/ActorCore, Unity Asset Store) | 18 gerçek WC hareketi: blok, yumruk, tekme, düşme | FBX (Mixamo uyumlu humanoid) | ticari kullanım OK (store EULA) | ~$31–45 |
| Motifect Martial Arts Motion Pack (itch.io) | 40 klip: karate, taekwondo, kung fu, güreş, duruşlar | FBX + BVH | "personal & commercial use in games" ücretsiz | 0 |
| Rokoko "6 free martial arts animations" | 6 klip, parmak dahil | FBX (Mixamo iskelet) | ticari OK | 0 (kayıt) |
| Bandai Namco Research Motiondataset | 3000+ klip, "fighting" kategorisi var | BVH | **CC BY-NC** — yayın için uygun değil | 0 |
| CMU Mocap DB | martial arts alt kümesi var (tam WC değil) | BVH | serbest | 0 |
| Mixamo | fist fight / kung fu genel | FBX | ticari OK | 0 (Adobe hesabı) |

Gerçek Wing Chun içeren tek paket Sidekick'inki. Diğerleri genel dövüş; Wing Chun'a özgü
Bong/Tan/Pak Sau ve chain punch'ı içermiyor.

### B. Videodan mocap (ücretsiz, esnek)
- **MoCapAnything V2** (SIGGRAPH Asia 2026, MIT lisans): tek kameralı videodan doğrudan BVH joint
  rotasyonu üretiyor, özel iskelet destekli. GPU önerilir; CPU'da yavaş ama tek kliplik denemeler yapılabilir.
- **FreeMoCap** (açık kaynak, çok kamera), Rokoko Video (ücretsiz, web).
- Kaynak video: kendi çektiğimiz veya CC lisanslı Siu Nim Tao / Chum Kiu form videoları.
- Kalite: parmaklar ve hızlı yumruklar sorunlu olabilir; Blender'da temizleme gerekir.

### C. Prosedürel keyframe (mevcut pipeline)
- Zaten Idle/Walk'u böyle yaptık; WC hareketleri geometrik olarak basit (dirsek centerline'da, düz hatlar)
  ve stilize karakterde iyi durur.
- Referans: teknik tanımları (açılar, sıralama) → `tools/anim_wingchun.py` içinde poz-keyframe tabloları.
- Sınır: Ağırlık aktarımı ve ince zamanlama "gerçek" mocap kadar inandırıcı olmaz.

## Karar önerisi
1. **Şimdi:** Prosedürel WC seti (C) — sıfır maliyet, cloud'da tamamen otomatik, kısa sürede oynanabilir prototip.
2. **Paralel:** Motifect paketini indirip (tarayıcıdan, itch.io) `assets/mocap/` altına koy → Blender'da
   humanoid rig'imize retarget denemesi; başarılıysa aynı yol Sidekick paketi için de çalışır.
3. **Prototip tutarsa:** Sidekick Wing Chun paketi (~$45) veya MoCapAnything ile kendi çekimlerimiz.

## Retarget yolu (Blender 5.2)
- Blender'a `File > Import > Motion Capture (.bvh)` veya FBX ile al
- Kemik isim eşlemesi: Mixamo (`mixamorig:LeftArm`) → bizim (`LeftUpperArm`) — script ile
- Godot tarafında alternatif: `SkeletonProfileHumanoid` + BoneMap ile retarget (import ayarı), Blender'a gerek kalmaz

# Ana karakter: Sokak stili Wing Chun dövüşçüsü

## Konsept (karar verildi)
- Stil: stilize low-poly, flat renk (bkz. ROADMAP)
- Kıyafet: **hoodie + jogger** + spor ayakkabı + el sargısı (wing chun/sokak dövüşü referansı)
- Palet: **distopik** — soluk/aşınmış koyu tonlar + tek sinyal rengi
  | Bölge | RGB (linear) | Not |
  |---|---|---|
  | Hoodie | 0.085 0.105 0.125 | mürekkep-petrol siyahı, aşınmış |
  | Kanguru cebi | 0.115 0.135 0.155 | bir ton açık |
  | Jogger | 0.34 0.31 0.27 | solmuş taupe |
  | Bacak yan şeridi / sargılar | 0.66 0.64 0.58 | kemik beyazı |
  | Sinyal rengi | 0.82 0.32 0.06 | hazard turuncusu: manşetler, merkez hat, kapüşon astarı, dirsek bandı |
  | Sneaker / taban | 0.07 0.07 0.08 / 0.60 0.58 0.53 | |
  | Ten / saç / göz | 0.78 0.62 0.52 / 0.10 0.08 0.07 / 0.04 0.04 0.05 | |
  | Maske | 0.05 0.055 0.06 | fight mode |

### İmza öğeleri (ikonik siluet için)
1. **Merkez hat**: göğüste dikey turuncu şerit — wing chun'un "centerline" ilkesine gönderme
2. **Asimetrik sargı**: sol ön kol (Man Sau kolu) dirseğe kadar bandajlı, dirsekte turuncu bant; sağ kol normal
3. **Top-knot**: buzz-cut + tepede küçük topuz — kung fu mirasına sokak yorumu
4. **Gözler**: iki dar koyu çizgi, kararlı bakış
5. **Fight mode**: kapüşon kapalı + yüz maskesi; kapüşonun turuncu astarı yüzü çerçeveler

### Fight mode (kapüşon kapalı) — oyun tasarımı notu
- glb içinde iki ayrı skinli obje: `HoodDown` (normalde görünür) ve `HoodUp` (kapüşon + astar + maske)
- Godot: `hero.gd` → `fight_mode` property görünürlükleri değiştirir
- Oyun fikri: fight mode bir "odak" hali — chain punch hızı ve hasar artar, bir odak sayacı tükenir;
  kapüşonu kapatma anı kısa bir animasyon + ses ile vurgulanır. Tasarımı Faz 3'te netleştireceğiz.
- Duruş: Yee Jee Kim Yeung Ma (içe dönük ayaklar, dizler kapalı), eller centerline'da Man Sau / Wu Sau
- Siluet: kompakt, dirsekler içeride; abartılı kas yok

## Rig eksen notları (prosedürel poz yazarken)
Blender XYZ euler: önce X, sonra Y, sonra Z; hepsi kemiğin **rest** eksenleri etrafında.
Uzuv kemikleri aşağı bakar (lokal Y = dünya -Z):
- X<0 öne savurma, X>0 arkaya
- Y: dikey eksen etrafında yaw — sol uzuvda Y>0 içe, sağda Y<0 içe
- Z: ön-arka ekseni etrafında roll — sol uzuvda Z<0 yana açma, sağda Z>0
Gövde kemikleri: X>0 öne eğilme, Z omurga etrafında dönme.

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

### C. Prosedürel keyframe (mevcut pipeline) — UYGULANDI
`tools/build_hero.py` içinde klipler: Stance (idle), Walk, ChainPunch, FrontKick, BongSau, TanSau, PakSau, Hit.
Poz tabloları derece cinsinden; `renders/hero_poses.png` kontak sayfasıyla gözle doğrulanıyor.
- Zaten Idle/Walk'u böyle yaptık; WC hareketleri geometrik olarak basit (dirsek centerline'da, düz hatlar)
  ve stilize karakterde iyi durur.
- Referans: teknik tanımları (açılar, sıralama) → `tools/anim_wingchun.py` içinde poz-keyframe tabloları.
- Sınır: Ağırlık aktarımı ve ince zamanlama "gerçek" mocap kadar inandırıcı olmaz.

## Karar önerisi
1. **Şimdi:** Prosedürel WC seti (C) — sıfır maliyet, cloud'da tamamen otomatik, kısa sürede oynanabilir prototip.
2. **Paralel:** Motifect paketini indirip (tarayıcıdan, itch.io) `assets/mocap/` altına koy → Blender'da
   humanoid rig'imize retarget denemesi; başarılıysa aynı yol Sidekick paketi için de çalışır.
3. **Prototip tutarsa:** Sidekick Wing Chun paketi (~$45) veya MoCapAnything ile kendi çekimlerimiz.

## Retarget yolu (Blender 5.2) — `tools/retarget_bvh.py`
- Kaynak iskeletin rest pozu önemsiz: her hero kemiği, eşleşen kaynak eklemleri arasındaki dünya yönüne "aim" edilir;
  Hips ve Chest iki vektörden (yukarı + sol-sağ) tam oryantasyon alır.
- İsim haritası Bandai, Mixamo ve UE-tarzı isimleri kapsar (`NAME_MAPS`).
- Sonuç NLA track olarak hero.blend'e eklenir ve hero.glb yeniden export edilir.
- Godot tarafında alternatif: `SkeletonProfileHumanoid` + BoneMap ile motor içi retarget.


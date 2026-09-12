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

## Gövde kaynağı (v4): Blender Studio Human Base Meshes (CC0)
- Paket: https://www.blender.org/download/demo-files/ → "Human Base Meshes Bundle v1.4.1" (CC0, atıf gerekmez)
- Kullanılan koleksiyon: "Body Male – Primitive (Stylized)" — 49 blok parça (göğüs, pelvis, omuz, kollar, parmaklı eller,
  ayaklar, kafa, göz, göz kapağı, burun, kulak). `tools/extract_base_mesh.py` ile
  `assets/characters/hero/base_male_primitive_stylized.blend` (175 KB) olarak repoya alındı.
- `build_hero.py` parçaları ekler, subsurf seviyesini uygular (`HERO_SUBSURF`, varsayılan 0 = köşeli low-poly, 1 = yumuşak),
  her parçaya materyal atar, birleştirir ve **vertex bandı deformasyonu** ile dövüşçü oranları verir:
  omuz/göğüs bandı x·1.16, boyun ·1.22, kollar ·1.28, ayaklar ·1.12.
- Bağlama: her parça tek kemiğe **rijit** vertex grubu (blok parçalar mankеn gibi eklemden döner; otomatik ağırlık
  parmak gibi küçük kapalı parçalarda başarısız oluyordu). Eklem pivotları parçaların yuvarlak uçlarının merkezinde.
- Tuzak: aynalı parçalar (.L/.R) aynı mesh verisini paylaşır; vertex grubu eklemeden önce `data.copy()` şart.
  Negatif ölçekli aynalar için birleştirme sonrası normaller yeniden hesaplanır.
- Kol kemikleri A-pozunda eğik olduğundan roll `GLOBAL_POS_Y` ile sabitlenir (eski dik kol ekseniyle aynı konvansiyon)
  ve tüm UpperArm pozlarına `ARM_REST_FIX` (14°) içe roll eklenir.
- Gözler: küre parçası; ön yüzler koyu iris, geri kalanı beyaz. Saç: kafa üstü/arkası "undercut" + tepede top-knot küresi.

### Kumaş kabukları (v4.1)
- Parçalı gövde "zırh plakası" gibi okunuyordu ve rijit bağlama diz/dirsekte boşluk bırakıyordu.
- Çözüm: hoodie ve jogger, ilgili parçaların kopyasının **voxel remesh**'i (0.016 m) → tek sürekli yüzey, normal boyunca
  12 mm şişirme, decimate (~1000 yüz), flat shading. Ağırlıklar gövdeden **DataTransfer (nearest face)** ile alınıp
  dikişlerde yumuşatılır; böylece kumaş eklemlerde gerilir, boşluk görünmez.
- Sol ön kol kabuğun dışında bırakılır (sargı + turuncu bant görünür kalır). Göğüs merkez hattı kabuğun önünde ince levha.
- Jogger yan şeridi denendi ve kaldırıldı (şişirilmiş kabuğun dışında havada kalıyordu); vurgu manşetlerde.

## Meshy.ai değerlendirmesi (Eylül 2026)
**Ne:** Metin/görselden 3D model üretimi, otomatik retopo/remesh, insansı auto-rig, 600+ animasyon kütüphanesi;
resmi MCP sunucusu (24 araç) ve REST API. Formatlar GLB/FBX/OBJ.
**Fiyat/lisans:** Free 100 kredi/ay, 10 indirme, çıktılar CC BY 4.0 (atıf şart). Pro 20$/ay 1000 kredi, tam ticari hak,
**API/MCP sadece Pro ve üstü**. Krediler devretmez.
**Bizim için artı:** hızlı konsept denemesi (bir prompt'la "Sifu tarzı sokak wing chun dövüşçüsü" görüp yönü test etmek),
sahne/prop/silah üretimi, base mesh alternatifi (2. seçenek yerine tek adımda texture'lı karakter).
**Eksi:** çıktılar texture'lı ve "yumuşak"; bizim flat-renk low-poly stiliyle uyuşmaz, remesh sonrası bile texture bağımlı.
Kapüşon açık/kapalı gibi varyantlar için tutarlılık garantisi yok. Rig kendi iskeleti → Godot BoneMap/retarget gerekir.
Cloud ortamımızda MCP kullanmak için Pro hesap + API anahtarı gerekir.
**Karar:** Ana karakter için şimdilik gereksiz; base mesh yaklaşımı tuttu. Üç durumda değerli: (1) kullanıcı konsept
görselleştirmesi istiyorsa, (2) 2. seçeneğe geçilirse texture'lı bir gövde kaynağı olarak, (3) Faz 2-3'te prop/çevre
asset'leri için. Free plan denemesi tarayıcıdan yapılabilir (API gerekmez), sonuç GLB olarak repoya konursa retarget
pipeline'ı üstünde çalışır.

Blender XYZ euler: önce X, sonra Y, sonra Z; hepsi kemiğin **rest** eksenleri etrafında.
Uzuv kemikleri aşağı bakar (lokal Y = dünya -Z):
- X<0 öne savurma, X>0 arkaya
- Y: dikey eksen etrafında yaw — sol uzuvda Y>0 içe, sağda Y<0 içe
- Z: ön-arka ekseni etrafında roll — sol uzuvda Z<0 yana açma, sağda Z>0
Gövde kemikleri: X>0 öne eğilme, Z omurga etrafında dönme.

**Depolama:** Pozlar derece/euler olarak yazılır ama rig tamamen QUATERNION modunda keyframe'lenir; Blender kemiğin
modundaki kanalı okuduğu için euler ve quaternion klipler aynı rig'de karışamaz (bu yüzden retarget sonrası mod geri çevrilmez).

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


## Meshy MCP — ilk deneme notları (Eylül 2026)
- MCP bağlantısı çalışıyor (`.mcp.json` + `MESHY_API_KEY`). Web arayüzünde üretilen modeller API'den **görünmüyor**
  (görev ve model listeleri boş); web'de üretilenler elle indirilip repoya konmalı. API ile üretilenler ise
  `meshy_download_model` ile doğrudan repoya iner.
- `meshy_get_task_status(wait=true)` MCP tarafında 60 sn'de zaman aşımına düşüyor; `wait=false` ile sorgulayıp
  REST üzerinden (`tools/meshy_api.py` veya curl) beklemek daha güvenilir.
- Test: metinden 3D "mook jong" (Meshy 6, 20 + doku 10 kredi). Mesh geldi, indirildi, Blender'a aktarıldı ama
  içerik yanlış: iki delikli silindir. **Ders:** niş/az bilinen objeler için metin→3D zayıf; önce
  `meshy_text_to_image` (3 kredi) ile referans görsel üret, beğen, sonra `meshy_image_to_3d`
  (smart-topology 15 kredi, meshy-7 30 kredi). Karakterde zaten bu yol izlendi ve sonuç çok iyiydi.
- Kredi tablosu: image-to-3d meshy-7 20 (+10 doku), smart-topology 5 (+10 doku), remesh 5, rig 5, animate 3.

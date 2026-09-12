# game99 Yol Haritası

## Karar: Motor seçimi (öneri: Godot 4)

| Kriter | Godot 4 | Unity | Unreal 5 |
|---|---|---|---|
| Cloud/headless çalışır mı? | **Evet** (bu repoda doğrulandı: import + run) | Hayır (lisans + GUI, Linux headless pratik değil) | Hayır (100+ GB, GPU ister) |
| Blender → motor pipeline | glTF native, sorunsuz | FBX/glTF (paket gerekli) | FBX tercih, glTF eklenti |
| Lisans / yayın maliyeti | MIT, ücretsiz, gelir payı yok | Ücretsiz katman, yıllık ciro sınırı | %5 royalty (1M$ üstü) |
| Öğrenme eğrisi | Düşük (GDScript, Python benzeri) | Orta (C#) | Yüksek (C++/Blueprint) |
| Grafik tavanı | Orta (Forward+ yeterli, AAA değil) | Yüksek | Çok yüksek |
| Repo boyutu / git dostu | Küçük, text tabanlı sahneler | Orta | Büyük, binary asset |

**Sonuç:** Bu ortamda (cloud, GPU yok) hem asset üretimi hem oyun tarafı sadece Godot ile otomatik olarak
test edilebiliyor. Prototip ve "playground" aşaması için Godot 4. Prototip başarılı olursa ve fotogerçekçi
grafik gerekirse Unreal'a geçiş değerlendirilebilir; glTF export'ları Unreal'a da taşınır.

## Karar: Görsel stil — stilize low-poly, flat renk

- Tek parça gövde: Blender **Skin modifier** ile prosedürel (edge iskeleti + yarıçaplar), 1 seviye subdivision, flat shading
- Texture yok: bölge bazlı düz materyaller (skin/hair/shirt/pants/boots/belt) → hızlı iterasyon, küçük dosya
- Kemik isimleri Godot **SkeletonProfileHumanoid** ile uyumlu (Hips, Spine, Chest, LeftUpperArm, ...) → ileride
  Mixamo vb. animasyonlar retarget edilebilir
- Gerekçe: GPU'suz cloud ortamında her şey Python ile üretilip headless test edilebiliyor; gerçekçi modelleme
  ve texture boyama bu ortamda verimsiz

## Fazlar

### Faz 0 — Ortam (TAMAMLANDI)
- [x] Blender 5.2.1 LTS headless çalışıyor (`tools/setup_cloud.sh`)
- [x] Godot 4.7.2 headless import/run çalışıyor
- [x] Blender → .glb → Godot döngüsü animasyonla doğrulandı

### Faz 1 — Ana karakter (DEVAM EDİYOR)
- [x] Stil kararı: stilize low-poly, flat renk paleti
- [x] `tools/build_hero.py`: Skin modifier ile tek parça gövde (607 vert / 602 face)
- [x] Rig: 19 kemik, Godot humanoid isimleri, otomatik weight
- [x] Animasyon: Idle (2s) + Walk (1s döngü), NLA üzerinden glb'ye export
- [x] Godot 4.7.2'de import + oynatma doğrulandı
- [x] Konsept: sokak stili wing chun dövüşçüsü — hoodie, jogger, distopik palet (`docs/CHARACTER.md`)
- [x] Prosedürel wing chun klipleri: Stance, ChainPunch, FrontKick, BongSau, TanSau, PakSau, Hit
- [x] BVH retarget scripti (`tools/retarget_bvh.py`), Bandai punch/kick ile test
- [x] v3 tasarım: imza öğeleri (merkez hat, asimetrik sargı, top-knot, gözler), fight mode (HoodUp/HoodDown objeleri)
- [x] Motifect paketi yüklendi; 8 klip retarget edildi (MT_Guard, MT_Combo, MT_Teep, MT_Elbow, MT_KickDefense, TKD_FrontKick, MT_Roundhouse, Judo_HipThrow)
- [x] v4 gövde: CC0 Blender Studio base mesh parçaları, dövüşçü oranları, rijit parça bağlama (docs/CHARACTER.md)
- [ ] Klip seçimi: hangi mocap klipleri oyunda kalacak, hangileri prosedürel WC klipleriyle harmanlanacak
- [x] v4.1 cilası: voxel remesh kumaş kabukları (hoodie/jogger), sarkan kapüşon, göz beyazı
- [x] Meshy Pro + MCP: konsept görsel → Meshy 7 mesh → Blender rig (mesafe skinning) → 18 klip; `hero_meshy.glb`
- [x] Meshy hero: doku, Meshy auto-rig ağırlıkları, kapüşon-açık varyant mesh'i (toplam ~81 kredi)
- [ ] Kapüşon-açık modele doku (10 kredi) ve iki model arasında fight-mode geçişi (Godot'ta iki sahne)
- [ ] Ana karakter kararı: Meshy hero (chibi) vs base-mesh hero (v4.1); base-mesh düşman/NPC üreticisi olarak kalır
- [ ] Run + Jump
- [ ] Siluet: el/ayak şekli, omuz genişliği; yüz detayı (basit göz/ağız)

### Faz 2 — Dünya + kontrol
- [ ] Godot: CharacterBody3D ile 3. şahıs kontrol (WASD + kamera)
- [ ] Basit test dünyası: zemin, birkaç engel, ışık, gökyüzü
- [ ] AnimationTree ile hareket-animasyon geçişleri

### Faz 3 — Dövüş, fight mode ve etkileşim
- [ ] Fight mode (kapüşon kapalı) mekaniği: odak sayacı, hız/hasar boost, geçiş animasyonu
- [ ] Blender'da 1-2 silah modeli, karaktere socket/bone attach
- [ ] Saldırı animasyonu, hitbox, basit düşman/hedef

### Faz 4 — Değerlendirme
- [ ] Prototip oynanabilir mi? Devam / motor değiştir / vazgeç kararı

## Klasör yapısı
```
tools/            Blender/Godot otomasyon scriptleri, kurulum
assets/characters Blender kaynak dosyaları (.blend)
assets/exports    Motor için glTF (.glb) çıktıları
renders/          Blender önizleme render'ları
game-godot/       Godot projesi
docs/             Kararlar, notlar
```

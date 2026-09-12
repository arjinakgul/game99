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
- [ ] Run + Jump animasyonları
- [ ] Siluet iyileştirme: saç hacmi, el/ayak şekli, omuz genişliği
- [ ] Yüz detayı (göz/ağız için basit geometri veya flat renk)

### Faz 2 — Dünya + kontrol
- [ ] Godot: CharacterBody3D ile 3. şahıs kontrol (WASD + kamera)
- [ ] Basit test dünyası: zemin, birkaç engel, ışık, gökyüzü
- [ ] AnimationTree ile hareket-animasyon geçişleri

### Faz 3 — Silahlar ve etkileşim
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

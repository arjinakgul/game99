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

## Fazlar

### Faz 0 — Ortam (TAMAMLANDI)
- [x] Blender 5.1.2 headless çalışıyor (`tools/setup_cloud.sh`)
- [x] Godot 4.5 headless import/run çalışıyor
- [x] Blender → .glb → Godot döngüsü animasyonla doğrulandı

### Faz 1 — Ana karakter
- [ ] Karakter konsepti: stil (low-poly / stilize / gerçekçi), siluet, renk paleti
- [ ] Blender'da prosedürel (Python) gövde modelleme, blok mesh yerine düzgün topoloji
- [ ] Rig: standart humanoid kemik isimleri (Mixamo/Godot uyumlu), IK
- [ ] Temel animasyonlar: idle, walk, run, jump
- [ ] Basit materyal / renk texture'ları

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

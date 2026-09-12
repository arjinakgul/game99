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

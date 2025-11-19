import flet as ft
import requests
from bs4 import BeautifulSoup
import threading
import time
import random

# --- AYARLAR ---
# Daha gerçekçi Android kimliği
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

CATEGORIES = {
    "Elektronik": "https://www.amazon.com.tr/s?k=elektronik&rh=p_8%3A10-",
    "Bilgisayar": "https://www.amazon.com.tr/s?k=bilgisayar&rh=p_8%3A10-",
    "Telefon": "https://www.amazon.com.tr/s?k=cep+telefonu&rh=p_8%3A10-",
    "Moda": "https://www.amazon.com.tr/s?k=giyim&rh=p_8%3A10-"
}

def main(page: ft.Page):
    page.title = "Amazon İndirim Avcısı"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    page.padding = 10
    
    # Hataları görmek için durum çubuğunu büyüttük
    status_text = ft.Text("Durum: Hazır", color="green", size=14, weight="bold")
    error_log = ft.Text("", color="red", size=12) # Hata detayları buraya gelecek
    
    data_table = ft.DataTable(
        column_spacing=10,
        columns=[
            ft.DataColumn(ft.Text("Kat.", size=12)),
            ft.DataColumn(ft.Text("%", size=12), numeric=True),
            ft.DataColumn(ft.Text("Ürün", size=12)),
            ft.DataColumn(ft.Text("Fiyat", size=12), numeric=True),
            ft.DataColumn(ft.Text("Link", size=12)),
        ],
        rows=[],
    )

    def add_row(category, discount, name, price, url):
        row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(category[:4], size=11)),
                ft.DataCell(ft.Container(content=ft.Text(discount, size=11, weight="bold", color="white"), bgcolor="green", padding=3, border_radius=3)),
                ft.DataCell(ft.Text(name[:15]+"..", size=11)),
                ft.DataCell(ft.Text(price.replace(" TL",""), size=11)),
                ft.DataCell(ft.IconButton(icon=ft.icons.OPEN_IN_NEW, icon_size=16, on_click=lambda _: page.launch_url(url))),
            ],
        )
        data_table.rows.insert(0, row)
        page.update()

    def scan_amazon():
        btn_start.disabled = True
        btn_stop.disabled = False
        page.update()
        
        page.session.set("running", True)
        
        while page.session.get("running"):
            for cat_name, url in CATEGORIES.items():
                if not page.session.get("running"): break
                
                status_text.value = f"Bağlanıyor: {cat_name}..."
                status_text.color = "blue"
                error_log.value = "" # Hata logunu temizle
                page.update()
                
                try:
                    res = requests.get(url, headers=HEADERS, timeout=10)
                    
                    # --- DEBUG KISMI: Hata Kodunu Kontrol Et ---
                    if res.status_code != 200:
                        status_text.value = f"HATA: Amazon Engelledi ({res.status_code})"
                        status_text.color = "red"
                        error_log.value = "Çözüm: İnternetini değiştirip tekrar dene."
                        page.update()
                        time.sleep(5) # Hata varsa biraz bekle
                        continue # Diğer kategoriye geç

                    soup = BeautifulSoup(res.content, "html.parser")
                    results = soup.find_all("div", {"data-component-type": "s-search-result"})
                    
                    if not results:
                        error_log.value = f"{cat_name} için ürün bulunamadı (Yapı değişmiş olabilir)."
                        page.update()

                    count = 0
                    for item in results:
                        try:
                            title = item.find("h2").text.strip()
                            link_tag = item.find("a", class_="a-link-normal")
                            if not link_tag: continue
                            link = "https://www.amazon.com.tr" + link_tag['href']
                            
                            price_whole = item.find("span", class_="a-price-whole")
                            price_frac = item.find("span", class_="a-price-fraction")
                            
                            if price_whole:
                                p_str = price_whole.text.strip().replace(",", "").replace(".", "")
                                frac = price_frac.text.strip() if price_frac else "00"
                                current_price = float(f"{p_str}.{frac}")
                                display_price = f"{current_price:.2f} TL"

                                old_elm = item.find("span", class_="a-text-price")
                                discount_display = "?"
                                if old_elm:
                                    off = old_elm.find("span", class_="a-offscreen")
                                    if off:
                                        o_str = off.text.replace("TL","").strip().replace(".","").replace(",",".")
                                        o_str = ''.join(c for c in o_str if c.isdigit() or c == '.')
                                        if o_str:
                                            old_price = float(o_str)
                                            if old_price > current_price:
                                                ratio = ((old_price - current_price) / old_price) * 100
                                                discount_display = f"%{ratio:.0f}"
                                
                                add_row(cat_name, discount_display, title, display_price, link)
                                count += 1
                        except:
                            continue
                    
                    status_text.value = f"{cat_name}: {count} ürün bulundu."
                    status_text.color = "green"
                    page.update()

                except Exception as e:
                    status_text.value = "Bağlantı Hatası!"
                    status_text.color = "red"
                    error_log.value = str(e)
                    page.update()

                # Rastgele bekleme (Robot gibi görünmemek için)
                time.sleep(random.uniform(3, 6))
            
            # Döngü sonu bekleme
            for i in range(60, 0, -1):
                if not page.session.get("running"): break
                if i % 5 == 0: # Her saniye güncellersek telefon kasar, 5sn'de bir güncelle
                    status_text.value = f"Bekleniyor: {i} sn..."
                    status_text.color = "orange"
                    page.update()
                time.sleep(1)

    def start_click(e):
        threading.Thread(target=scan_amazon, daemon=True).start()

    def stop_click(e):
        page.session.set("running", False)
        status_text.value = "Durduruldu."
        status_text.color = "red"
        btn_start.disabled = False
        btn_stop.disabled = True
        page.update()

    btn_start = ft.ElevatedButton("Başlat", on_click=start_click, bgcolor="green", color="white")
    btn_stop = ft.ElevatedButton("Durdur", on_click=stop_click, bgcolor="red", color="white", disabled=True)

    page.add(
        ft.Text("Amazon İndirim Avcısı v2", size=20, weight="bold"),
        ft.Row([btn_start, btn_stop]),
        status_text,
        error_log, # Hata detaylarını buraya yazacak
        ft.Column([data_table], scroll="adaptive", expand=True)
    )

ft.app(target=main)

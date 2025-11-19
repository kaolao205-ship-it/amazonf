import flet as ft
import requests
from bs4 import BeautifulSoup
import threading
import time

# --- AYARLAR ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "tr-TR"
}

# Kategoriler sözlük yapısında olmalı. Tırnaklara ve virgüllere dikkat.
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
    
    status_text = ft.Text("Durum: Hazır", color="grey", size=12)
    
    # Mobilde tabloyu sığdırmak için sütun aralıklarını azalttık
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
                ft.DataCell(ft.Text(category[:4], size=11)), # Kategori ismini kısalttık (Elek.)
                ft.DataCell(ft.Container(content=ft.Text(discount, size=11, weight="bold", color="white"), bgcolor="green", padding=3, border_radius=3)),
                ft.DataCell(ft.Text(name[:15]+"..", size=11)), # İsmi kısalttık
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
                
                status_text.value = f"Bakılıyor: {cat_name}..."
                page.update()
                
                try:
                    res = requests.get(url, headers=HEADERS)
                    soup = BeautifulSoup(res.content, "html.parser")
                    results = soup.find_all("div", {"data-component-type": "s-search-result"})
                    
                    if not results:
                        print(f"{cat_name} için sonuç bulunamadı.")

                    for item in results:
                        try:
                            title = item.find("h2").text.strip()
                            link = "https://www.amazon.com.tr" + item.find("a", class_="a-link-normal")['href']
                            
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
                                        # Temizlik (Invisible characters fix)
                                        o_str = ''.join(c for c in o_str if c.isdigit() or c == '.')
                                        if o_str:
                                            old_price = float(o_str)
                                            if old_price > current_price:
                                                ratio = ((old_price - current_price) / old_price) * 100
                                                discount_display = f"%{ratio:.0f}"
                                
                                # Sadece indirim oranı hesaplanabilenleri veya bariz ucuzları ekle
                                add_row(cat_name, discount_display, title, display_price, link)

                        except Exception as e:
                            continue
                except Exception as e:
                    status_text.value = f"Hata: {str(e)}"
                    page.update()

                time.sleep(2)
            
            status_text.value = "Bekleniyor (60sn)..."
            page.update()
            for _ in range(60):
                if not page.session.get("running"): break
                time.sleep(1)

    def start_click(e):
        threading.Thread(target=scan_amazon, daemon=True).start()

    def stop_click(e):
        page.session.set("running", False)
        status_text.value = "Durduruldu."
        btn_start.disabled = False
        btn_stop.disabled = True
        page.update()

    btn_start = ft.ElevatedButton("Başlat", on_click=start_click, bgcolor="green", color="white")
    btn_stop = ft.ElevatedButton("Durdur", on_click=stop_click, bgcolor="red", color="white", disabled=True)

    page.add(
        ft.Text("Amazon İndirim Avcısı", size=20, weight="bold"),
        ft.Row([btn_start, btn_stop]),
        status_text,
        ft.Column([data_table], scroll="adaptive", expand=True)
    )

ft.app(target=main)

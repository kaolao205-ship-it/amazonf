import flet as ft
import requests
from bs4 import BeautifulSoup
import threading
import time

# --- AYARLAR ---
HEADERS = {
    User-Agent Mozilla5.0 (Windows NT 10.0; Win64; x64) AppleWebKit537.36 (KHTML, like Gecko) Chrome114.0.0.0 Safari537.36,
    Accept-Language tr-TR
}

CATEGORIES = {
    Elektronik httpswww.amazon.com.trsk=elektronik&rh=p_8%3A10-,
    Bilgisayar httpswww.amazon.com.trsk=bilgisayar&rh=p_8%3A10-,
    Telefon httpswww.amazon.com.trsk=cep+telefonu&rh=p_8%3A10-,
    Moda httpswww.amazon.com.trsk=giyim&rh=p_8%3A10-
}

def main(page ft.Page)
    page.title = Amazon İndirim Avcısı
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = adaptive
    
    # --- UI Elemanları ---
    status_text = ft.Text(Durum Hazır, color=grey)
    
    # Tablo (Liste) Yapısı
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(Kat.)),
            ft.DataColumn(ft.Text(% İnd.)),
            ft.DataColumn(ft.Text(Ürün)),
            ft.DataColumn(ft.Text(Fiyat)),
            ft.DataColumn(ft.Text(Git)),
        ],
        rows=[],
    )

    def add_row(category, discount, name, price, url)
        # Satır Ekleme Fonksiyonu
        row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(category, size=10)),
                ft.DataCell(ft.Container(content=ft.Text(discount, weight=bold, color=white), bgcolor=green, padding=5, border_radius=5)),
                ft.DataCell(ft.Text(name[30]+..., size=12)), # Mobilde yer az diye ismi kısaltıyoruz
                ft.DataCell(ft.Text(price, size=12)),
                ft.DataCell(ft.IconButton(icon=ft.icons.OPEN_IN_NEW, on_click=lambda _ page.launch_url(url))),
            ],
        )
        data_table.rows.insert(0, row) # En üste ekle
        page.update()

    def scan_amazon()
        btn_start.disabled = True
        btn_stop.disabled = False
        page.update()
        
        page.session.set(running, True)
        
        while page.session.get(running)
            for cat_name, url in CATEGORIES.items()
                if not page.session.get(running) break
                
                status_text.value = fTaranıyor {cat_name}...
                page.update()
                
                try
                    res = requests.get(url, headers=HEADERS)
                    soup = BeautifulSoup(res.content, html.parser)
                    results = soup.find_all(div, {data-component-type s-search-result})
                    
                    for item in results
                        try
                            title = item.find(h2).text.strip()
                            link = httpswww.amazon.com.tr + item.find(a, class_=a-link-normal)['href']
                            
                            price_whole = item.find(span, class_=a-price-whole)
                            price_frac = item.find(span, class_=a-price-fraction)
                            
                            if price_whole
                                # Fiyat Temizleme
                                p_str = price_whole.text.strip().replace(,, ).replace(., )
                                frac = price_frac.text.strip() if price_frac else 00
                                current_price = float(f{p_str}.{frac})
                                display_price = f{current_price} TL

                                # Eski Fiyat
                                old_elm = item.find(span, class_=a-text-price)
                                discount_display = 
                                if old_elm
                                    off = old_elm.find(span, class_=a-offscreen)
                                    if off
                                        o_str = off.text.replace(TL,).strip().replace(.,).replace(,,.)
                                        old_price = float(o_str)
                                        if old_price  current_price
                                            ratio = ((old_price - current_price)  old_price)  100
                                            discount_display = f%{ratio.0f}

                                # Aynı ürünü tekrar eklememek için basit kontrol (gerçek appte id kontrolü gerekir)
                                add_row(cat_name, discount_display, title, display_price, link)

                        except
                            continue
                except Exception as e
                    print(e)

                time.sleep(2)
            
            # Bekleme Süresi (Demo için kısa)
            status_text.value = Bekleniyor...
            page.update()
            time.sleep(60) # 1 dakika bekle

    def start_click(e)
        threading.Thread(target=scan_amazon, daemon=True).start()

    def stop_click(e)
        page.session.set(running, False)
        status_text.value = Durduruldu.
        btn_start.disabled = False
        btn_stop.disabled = True
        page.update()

    # Butonlar
    btn_start = ft.ElevatedButton(Başlat, on_click=start_click, bgcolor=green, color=white)
    btn_stop = ft.ElevatedButton(Durdur, on_click=stop_click, bgcolor=red, color=white, disabled=True)

    page.add(
        ft.Text(Amazon İndirim Avcısı (Mobil), size=20, weight=bold),
        ft.Row([btn_start, btn_stop]),
        status_text,
        ft.Column([data_table], scroll=adaptive, height=500) # Scroll edilebilir alan
    )

ft.app(target=main)
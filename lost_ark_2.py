import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import ctypes
import queue
import threading
import sys

class HoverButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = self['activebackground']

    def on_leave(self, e):
        self['background'] = self.defaultBackground

def fetch_data(result_queue):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        result_queue.put(["Error: Playwright not found"])
        return

    try:
        executable_path = None
        if getattr(sys, 'frozen', False):
            # 如果是打包後的執行檔
            executable_path = os.path.join(sys._MEIPASS, 'chromium', 'chrome.exe')
        
        with sync_playwright() as p:
            browser_type = p.chromium
            browser = browser_type.launch(headless=True, executable_path=executable_path)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            page = context.new_page()
            
            url = "https://www.dd373.com/s-1w5rsv-rmn8x6-s4habc-0-0-0-b9dbv6-0-0-0-0-0-1-0-5-0.html"
            
            try:
                page.goto(url, timeout=60000)
                page.wait_for_timeout(5000)
                page.wait_for_selector(".width233.p-l30 .font12.colorFF5", timeout=60000)
                elements = page.query_selector_all(".width233.p-l30 .font12.colorFF5")
                titles = page.query_selector_all(".goods-list-title")
                
                values = []
                prices = []
                links = []
                for element, title in zip(elements[:5], titles[:5]):
                    value = float(element.inner_text().split('=')[1].strip().split('金')[0])
                    price = float(title.inner_text().split('=')[1].strip().split('元')[0])
                    link = title.get_attribute('href')
                    if link:
                        link = "https://www.dd373.com" + link
                    values.append(value)
                    prices.append(price)
                    links.append(link)
                
                result_queue.put((values, prices, links))
            except Exception as e:
                print(f"發生錯誤: {e}")
                result_queue.put(["Error: " + str(e)])
            finally:
                browser.close()
    except Exception as e:
        print(f"Playwright 錯誤: {e}")
        result_queue.put(["Error: Playwright failed to initialize: " + str(e)])

def update_prices():
    status_var.set("正在更新價格...")
    progress_bar.start(10)
    result_queue = queue.Queue()
    threading.Thread(target=fetch_data, args=(result_queue,), daemon=True).start()
    root.after(100, check_queue, result_queue)

def check_queue(result_queue):
    try:
        result = result_queue.get_nowait()
        if isinstance(result, tuple) and len(result) == 3:
            values, prices, links = result
            if values and not any(isinstance(value, str) and value.startswith("Error") for value in values):
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                update_time_var.set(f"更新時間: {current_time}")
                for i, (value, price, link) in enumerate(zip(values, prices, links)):
                    price_vars[i].set(f"{value:.2f} (價格: {price:.2f}元)")
                    price_links[i] = link  # 儲存連結
                
                average = sum(values) / len(values)
                twd_rate = average / 4.5
                average_var.set(f"{average:.2f}")
                twd_rate_var.set(f"{twd_rate:.2f}")
                
                status_var.set("價格更新成功")
            else:
                error_message = values[0] if values else "無法獲取價格"
                status_var.set(error_message)
        else:
            error_message = result[0] if result else "無法獲取價格"
            status_var.set(error_message)
        progress_bar.stop()
        root.after(10000, update_prices)  # 每10秒更新一次
    except queue.Empty:
        root.after(100, check_queue, result_queue)

def calculate_diamonds_per_currency():
    try:
        coins_per_currency = float(entry_diamonds_coins_per_currency.get())
        coins_amount_for_diamonds = float(entry_coins_amount_for_diamonds.get())

        diamonds_per_coin = 90 / coins_amount_for_diamonds
        rmb_per_twd = 4.5

        if selected_currency.get() == "TWD":
            diamonds_per_currency = diamonds_per_coin * coins_per_currency
        elif selected_currency.get() == "RMB":
            twd_equivalent = coins_per_currency / rmb_per_twd
            diamonds_per_currency = diamonds_per_coin * twd_equivalent
        else:
            result_label_diamonds.config(text="請選擇貨幣單位")
            return

        diamonds_per_currency = round(diamonds_per_currency, 1)
        result_label_diamonds.config(text=f"1台幣約等於 {diamonds_per_currency} 藍鑽")
    except ValueError:
        messagebox.showerror("錯誤", "請輸入有效的數字")

def calculate_pein_value():
    try:
        coins_per_90_diamonds = float(entry_coins_per_90_diamonds.get())
        coins_per_diamond = coins_per_90_diamonds / 90

        item_values = {
            "沛恩": 6.5,
            "高級恢復藥": 0.3,
            "精靈恢復藥與炸彈": 1,
            "手榴彈": 0.83,
            "榮譽碎片(中)": (coins_per_diamond * 120 / 7500) * 1000
        }

        selected_item_value = item_values.get(selected_item.get())

        if selected_item_value is not None:
            value_in_coins = coins_per_diamond * selected_item_value
            result_label_pein.config(text=f"1個{selected_item.get()}約等於 {round(value_in_coins)} 金幣")
        else:
            result_label_pein.config(text="請選擇要計算的項目")
    except ValueError:
        messagebox.showerror("錯誤", "請輸入有效的數字")



root = tk.Tk()
root.title("Lost Ark 價格監控與計算器")
root.geometry("500x600")
root.configure(bg='#1e1e1e')
icon_path = r'C:\Users\m6g4f\OneDrive\文件\python\2.ico'
root.iconbitmap(icon_path)


style = ttk.Style()
style.theme_use('clam')
style.configure('TFrame', background='#1e1e1e')
style.configure('TLabel', background='#1e1e1e', foreground='#ffffff', font=('Roboto', 10))
style.configure('TButton', font=('Roboto', 10))
style.configure('TProgressbar', thickness=5)
style.configure('TNotebook', background='#1e1e1e')
style.configure('TNotebook.Tab', background='#2e2e2e', foreground='#ffffff', padding=[10, 5])
style.map('TNotebook.Tab', background=[('selected', '#3e3e3e')], foreground=[('selected', '#4CAF50')])

# 新增：配置 Radiobutton 樣式
style.configure('TRadiobutton', background='#1e1e1e', foreground='#ffffff', font=('Roboto', 10))
style.map('TRadiobutton', background=[('active', '#1e1e1e')], foreground=[('active', '#4CAF50')])

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# DD373 價格監控標籤頁
frame_dd373 = ttk.Frame(notebook)
notebook.add(frame_dd373, text="DD373 價格監控")

title_label = ttk.Label(frame_dd373, text="DD373 價格監控", font=('Roboto', 18, 'bold'), foreground='#4CAF50')
title_label.pack(pady=(20, 10))

update_time_var = tk.StringVar()
update_time_label = ttk.Label(frame_dd373, textvariable=update_time_var, font=('Roboto', 10, 'italic'))
update_time_label.pack(pady=(0, 10))

price_frame = ttk.Frame(frame_dd373)
price_frame.pack(pady=10)

price_vars = [tk.StringVar() for _ in range(5)]
price_links = [None] * 5  # 儲存連結的列表

def open_link(index):
    if price_links[index]:
        import webbrowser
        webbrowser.open(price_links[index])

for i in range(5):
    ttk.Label(price_frame, text=f"最佳比值 #{i + 1}:", font=('Roboto', 11)).grid(row=i, column=0, sticky='e', padx=(0, 10), pady=5)
    link_label = ttk.Label(price_frame, textvariable=price_vars[i], font=('Roboto', 11, 'bold'), foreground='#2196F3', cursor="hand2")
    link_label.grid(row=i, column=1, sticky='w', columnspan=2, pady=5)
    link_label.bind("<Button-1>", lambda e, i=i: open_link(i))

average_frame = ttk.Frame(frame_dd373)
average_frame.pack(pady=10)

average_var = tk.StringVar()
twd_rate_var = tk.StringVar()

ttk.Label(average_frame, text="平均值:", font=('Roboto', 11)).grid(row=0, column=0, sticky='e', padx=(0, 10), pady=5)
ttk.Label(average_frame, textvariable=average_var, font=('Roboto', 11, 'bold'), foreground='#FFC107').grid(row=0, column=1, sticky='w', pady=5)
ttk.Label(average_frame, text="金/人民幣", font=('Roboto', 11)).grid(row=0, column=2, sticky='w', padx=(5, 0), pady=5)

ttk.Label(average_frame, text="台幣比率:", font=('Roboto', 11)).grid(row=1, column=0, sticky='e', padx=(0, 10), pady=5)
ttk.Label(average_frame, textvariable=twd_rate_var, font=('Roboto', 11, 'bold'), foreground='#FFC107').grid(row=1, column=1, sticky='w', pady=5)
ttk.Label(average_frame, text="金/台幣", font=('Roboto', 11)).grid(row=1, column=2, sticky='w', padx=(5, 0), pady=5)

status_var = tk.StringVar()
status_label = ttk.Label(frame_dd373, textvariable=status_var, font=('Roboto', 10, 'italic'), foreground='#FFC107')
status_label.pack(pady=(10, 0))

progress_bar = ttk.Progressbar(frame_dd373, mode='indeterminate', length=300)
progress_bar.pack(pady=(10, 0))

update_button = HoverButton(frame_dd373, text="立即更新", command=update_prices, 
                            bg='#4CAF50', fg='white', activebackground='#45a049', activeforeground='white',
                            font=('Roboto', 10, 'bold'), relief=tk.FLAT, padx=10, pady=5)
update_button.pack(pady=(20, 0))

# 藍鑽換算器標籤頁
frame_diamonds = ttk.Frame(notebook)
notebook.add(frame_diamonds, text="藍鑽換算器")

selected_currency = tk.StringVar(value="TWD")

ttk.Label(frame_diamonds, text="選擇貨幣單位", font=('Roboto', 12, 'bold')).pack(pady=(20, 10))
ttk.Radiobutton(frame_diamonds, text="台幣 (TWD)", variable=selected_currency, value="TWD").pack(anchor='w', padx=20)
ttk.Radiobutton(frame_diamonds, text="人民幣 (RMB)", variable=selected_currency, value="RMB").pack(anchor='w', padx=20)

ttk.Label(frame_diamonds, text="請輸入該幣值1元等於多少金幣").pack(pady=(20, 5))
entry_diamonds_coins_per_currency = ttk.Entry(frame_diamonds)
entry_diamonds_coins_per_currency.pack(pady=5)

ttk.Label(frame_diamonds, text="請輸入多少金幣可以換90藍鑽").pack(pady=(20, 5))
entry_coins_amount_for_diamonds = ttk.Entry(frame_diamonds)
entry_coins_amount_for_diamonds.pack(pady=5)

calculate_button = HoverButton(frame_diamonds, text="計算藍鑽", command=calculate_diamonds_per_currency,
                               bg='#4CAF50', fg='white', activebackground='#45a049', activeforeground='white',
                               font=('Roboto', 10, 'bold'), relief=tk.FLAT, padx=10, pady=5)
calculate_button.pack(pady=(20, 10))

result_label_diamonds = ttk.Label(frame_diamonds, text="", font=('Roboto', 12, 'bold'), foreground='#FFC107')
result_label_diamonds.pack(pady=10)

# 商城物品計算器標籤頁
frame_pein = ttk.Frame(notebook)
notebook.add(frame_pein, text="商城物品計算器")

ttk.Label(frame_pein, text="輸入 90 藍鑽等於多少金幣", font=('Roboto', 12, 'bold')).pack(pady=(20, 10))
entry_coins_per_90_diamonds = ttk.Entry(frame_pein, width=30)
entry_coins_per_90_diamonds.pack(pady=10)

selected_item = tk.StringVar(value=None)
items = ["沛恩", "高級恢復藥", "精靈恢復藥與炸彈", "手榴彈", "榮譽碎片(中)"]

ttk.Label(frame_pein, text="選擇要計算的項目", font=('Roboto', 12, 'bold')).pack(pady=(20, 10))
for item in items:
    ttk.Radiobutton(frame_pein, text=item, variable=selected_item, value=item).pack(anchor='w', padx=20, pady=5)

calculate_button_pein = HoverButton(frame_pein, text="計算", command=calculate_pein_value,
                                    bg='#4CAF50', fg='white', activebackground='#45a049', activeforeground='white',
                                    font=('Roboto', 10, 'bold'), relief=tk.FLAT, padx=10, pady=5)
calculate_button_pein.pack(pady=(20, 10))

result_label_pein = ttk.Label(frame_pein, text="", font=('Roboto', 12, 'bold'), foreground='#FFC107')
result_label_pein.pack(pady=10)

# 添加 "BY HUGO" 標籤
ttk.Label(root, text="BY Hugo", font=('Roboto', 8, 'italic'), foreground='#888888').pack(side='bottom', anchor='se', padx=10, pady=5)

update_prices()  # 開始更新價格
root.mainloop()
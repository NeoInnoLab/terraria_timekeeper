
# Terraria Timekeeper (Windows)

一個超簡單的小程式，幫你在玩 **Terraria** 時做時間管理：

- 設定「玩幾小時/分鐘/秒」或「玩到幾點（24h）」
- 背景監控 `Terraria.exe`
- 在結束前 **5 / 3 / 1 分鐘** 顯示通知（Toast 通知 + 彈出視窗提醒）
- 如果你 **比預期更早關掉** 遊戲，依「提前分鐘數」給獎勵點數，並記錄到 `rewards_log.csv`
- 總點數會存到 `rewards_total.json`
- **兩種 GUI 版本**：PySimpleGUI（經典版）和 Kivy（現代版）

> 預設每提前 1 分鐘 = **+10 點**。你可以在原始碼中修改 `POINTS_PER_MIN_EARLY`。

## 🎮 版本選擇

### PySimpleGUI 版本（經典版）
- 檔案：`terraria_timekeeper.py`
- 特色：穩定、輕量、相容性好
- 適合：一般使用者

### Kivy 版本（現代版）
- 檔案：`terraria_timekeeper_kivy.py`
- 特色：現代化 GUI、Terraria 風格背景、跨平台支援
- 適合：追求視覺效果的玩家

---

## 安裝步驟（Windows）

1. 安裝 Python（3.9 或以上）。  
2. 下載本專案檔案，解壓縮到任意資料夾。
3. **重要：確保使用正確的 Python 環境**
   - 如果使用 conda：`conda activate py39`
   - 或直接使用批次檔：`run_terraria_timekeeper.bat` 或 `run_terraria_timekeeper_kivy.bat`
4. 在該資料夾開啟命令列，安裝套件：

### PySimpleGUI 版本：
```bash
pip install -r requirements.txt
```

### Kivy 版本：
```bash
pip install -r requirements_kivy.txt
```

5. 執行：

### PySimpleGUI 版本：
```bash
python terraria_timekeeper.py
```

### Kivy 版本：
```bash
python terraria_timekeeper_kivy.py
```

---

## 使用方式

### 基本操作（兩個版本相同）
1. 選擇模式：
   - **玩幾小時/分鐘/秒數**：輸入小時分鐘秒數。
   - **玩到幾點（HH:MM）**：24 小時制；若時間已過，會自動算到隔天同一時刻。
2. 按 **開始**。
3. 程式會在背景監控並在剩餘 **5/3/1 分鐘** 彈出通知視窗（包含 Toast 通知與彈出視窗提醒）。
   - 5/3/1分鐘時，僅會出現該時間的彈出視窗提醒。例如:1分鐘到的時候，僅跳出1分鐘通知，不會同時出現5, 3, 1分鐘的通知。
   - 點選提醒視窗上面的 OK 確認按鈕，會把該提醒視窗關閉
4. 若你在時間到之前就關掉 Terraria，會依提前分鐘數加點，記錄到：
   - `rewards_log.csv`（詳細紀錄）
   - `rewards_total.json`（總點數）

### Kivy 版本特色
- **Terraria 風格背景**：像素藝術風格的天空、山脈和太陽
- **現代化介面**：300x400 視窗，清晰的文字和按鈕
- **跨平台支援**：支援 Windows、macOS、Linux、Android、iOS
- **響應式設計**：自動適應不同螢幕尺寸

> 注意：就算你開始計時時 Terraria 尚未啟動，計時依然會走；「提前」獎勵只有在 **遊戲關閉時** 且 **尚未到時間** 才會觸發。

---

## 打包成 EXE（可選）

若要做成單一 EXE 檔（方便雙擊執行），可用 [PyInstaller]:

### PySimpleGUI 版本：
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name TerrariaTimekeeper terraria_timekeeper.py
```

### Kivy 版本：
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name TerrariaTimekeeperKivy terraria_timekeeper_kivy.py
```

打包後，EXE 會在 `dist/` 目錄。

---

## 客製化

- 更換監控的程式名稱：修改原始碼 `PROCESS_NAME = "Terraria.exe"`。
- 調整提醒時間：在 `MonitorThread.run()` 中的 `(5, 3, 1)` 列表新增/移除即可。
- 調整提前獎勵點數：修改 `POINTS_PER_MIN_EARLY` 常數。

---

## 常見問題

- **通知沒跳出？**  
  確認已安裝 `win10toast`，且未被系統通知設定關閉。如果仍無，程式會退而在主控台列印訊息。

- **沒有找到 Terraria.exe？**  
  只要進程名稱不是 `Terraria.exe`（例如使用不同啟動器/可執行檔名），請把 `PROCESS_NAME` 改成正確的檔名。

- **Kivy 版本無法啟動？**  
  確保已安裝 Kivy 和相關依賴套件：`pip install -r requirements_kivy.txt`

- **文字太小或重疊？**  
  Kivy 版本已優化為 300x400 視窗，如果仍有問題，可以調整 `Window.size` 設定。

## 📁 專案檔案結構

```
terraria_timekeeper/
├── terraria_timekeeper.py          # PySimpleGUI 版本（經典版）
├── terraria_timekeeper_kivy.py     # Kivy 版本（現代版）
├── requirements.txt                # PySimpleGUI 版本依賴
├── requirements_kivy.txt           # Kivy 版本依賴
├── run_terraria_timekeeper.bat     # PySimpleGUI 版本啟動檔
├── run_terraria_timekeeper_kivy.bat # Kivy 版本啟動檔
├── README.md                       # 使用說明
├── README_KIVY.md                  # Kivy 版本詳細說明
├── CURSOR_COLLABORATION_GUIDE.md   # 開發歷程記錄
├── rewards_log.csv                 # 獎勵記錄（執行後產生）
└── rewards_total.json              # 總點數記錄（執行後產生）
```

---

Enjoy & 自律贏一半！🎮

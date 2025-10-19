# Terraria Timekeeper - Kivy GUI Version

一個使用 Kivy GUI 框架的超簡單小程式，幫你在玩 **Terraria** 時做時間管理：

- 設定「玩幾小時/分鐘/秒」或「玩到幾點（24h）」
- 背景監控 `Terraria.exe`
- 在結束前 **5 / 3 / 1 分鐘** 顯示通知（右下角彈出 + Kivy 彈出視窗）
- 如果你 **比預期更早關掉** 遊戲，依「提前分鐘數」給獎勵點數，並記錄到 `rewards_log.csv`
- 總點數會存到 `rewards_total.json`

> 預設每提前 1 分鐘 = **+10 點**。你可以在原始碼中修改 `POINTS_PER_MIN_EARLY`。

---

## 安裝步驟（Windows）

1. 安裝 Python（3.9 或以上）。  
2. 下載本專案檔案，解壓縮到任意資料夾。
3. **重要：確保使用正確的 Python 環境**
   - 如果使用 conda：`conda activate py39`
   - 或直接使用：`run_terraria_timekeeper_kivy.bat`（已包含環境設定）
4. 在該資料夾開啟命令列，安裝套件：

```bash
pip install -r requirements_kivy.txt
```

5. 執行：

```bash
python terraria_timekeeper_kivy.py
```

或直接雙擊 `run_terraria_timekeeper_kivy.bat`

---

## 使用方式

1. 選擇模式：
   - **玩幾小時/分鐘/秒數**：輸入小時分鐘秒數。
   - **玩到幾點（HH:MM）**：24 小時制；若時間已過，會自動算到隔天同一時刻。
2. 按 **開始**。
3. 程式會在背景監控並在剩餘 **5/3/1 分鐘** 彈出通知視窗（包含 Toast 通知與 Kivy 彈出視窗提醒）。
   - 5/3/1分鐘時，僅會出現該時間的彈出視窗提醒。例如:1分鐘到的時候，僅跳出1分鐘通知，不會同時出現5, 3, 1分鐘的通知。
   - 點選提醒視窗上面的 OK 確認按鈕，會把該提醒視窗關閉
4. 若你在時間到之前就關掉 Terraria，會依提前分鐘數加點，記錄到：
   - `rewards_log.csv`（詳細紀錄）
   - `rewards_total.json`（總點數）

> 注意：就算你開始計時時 Terraria 尚未啟動，計時依然會走；「提前」獎勵只有在 **遊戲關閉時** 且 **尚未到時間** 才會觸發。

---

## Kivy GUI 特色功能

### 現代化介面
- **響應式設計**：自動適應不同螢幕尺寸
- **直觀操作**：清晰的按鈕和輸入框
- **即時狀態**：Terraria 運行狀態即時顯示
- **進度條**：視覺化顯示剩餘時間進度

### 彈出視窗提醒
- **5/3/1 分鐘提醒**：精確時機的 Kivy 彈出視窗
- **時間到通知**：清晰的遊戲結束提醒
- **提前結束獎勵**：慶祝通知與點數追蹤
- **手動關閉**：所有彈出視窗都提供 OK 按鈕

### 多執行緒支援
- **背景監控**：不影響 GUI 響應性
- **即時更新**：狀態和時間即時更新
- **安全退出**：正確處理執行緒結束

---

## 打包成 EXE（可選）

若要做成單一 EXE 檔（方便雙擊執行），可用 [PyInstaller]：

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
- 修改 GUI 外觀：調整 Kivy 的顏色、字體大小等屬性。

---

## Kivy vs PySimpleGUI 比較

| 功能 | PySimpleGUI 版本 | Kivy 版本 |
|------|------------------|-----------|
| GUI 框架 | PySimpleGUI | Kivy |
| 跨平台支援 | 良好 | 優秀 |
| 自訂外觀 | 有限 | 豐富 |
| 響應式設計 | 基本 | 優秀 |
| 動畫效果 | 無 | 支援 |
| 觸控支援 | 無 | 支援 |
| 效能 | 良好 | 優秀 |
| 學習曲線 | 簡單 | 中等 |

---

## 常見問題

- **Kivy 安裝失敗？**  
  確保已安裝正確的 Python 版本和相依套件。某些情況下需要安裝額外的系統依賴。

- **通知沒跳出？**  
  確認已安裝 `win10toast`，且未被系統通知設定關閉。如果仍無，程式會退而在主控台列印訊息。

- **沒有找到 Terraria.exe？**  
  只要進程名稱不是 `Terraria.exe`（例如使用不同啟動器/可執行檔名），請把 `PROCESS_NAME` 改成正確的檔名。

- **Kivy 視窗無法關閉？**  
  使用右上角的 X 按鈕或點擊 Exit 按鈕來關閉應用程式。

---

## 技術特色

### Kivy 框架優勢
- **跨平台**：支援 Windows、macOS、Linux、Android、iOS
- **GPU 加速**：使用 OpenGL ES 2.0 進行硬體加速
- **觸控友善**：原生支援觸控和手勢操作
- **高度可自訂**：豐富的樣式和主題選項

### 程式架構
- **MVVM 模式**：清晰的模型-視圖-視圖模型分離
- **多執行緒**：背景監控不影響 GUI 響應
- **事件驅動**：使用 Kivy 的 Clock 進行 UI 更新
- **資源管理**：正確的執行緒和資源清理

---

Enjoy & 自律贏一半！🎮

## 開發者資訊

- **框架**：Kivy 2.1.0+
- **Python 版本**：3.9+
- **作業系統**：Windows 10/11（跨平台支援）
- **授權**：MIT License

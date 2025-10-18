
# Terraria Timekeeper (Windows)

一個超簡單的小程式，幫你在玩 **Terraria** 時做時間管理：

- 設定「玩幾小時/分鐘」或「玩到幾點（24h）」
- 背景監控 `Terraria.exe`
- 在結束前 **5 / 3 / 1 分鐘** 顯示通知（右下角彈出）
- 如果你 **比預期更早關掉** 遊戲，依「提前分鐘數」給獎勵點數，並記錄到 `rewards_log.csv`
- 總點數會存到 `rewards_total.json`

> 預設每提前 1 分鐘 = **+10 點**。你可以在原始碼中修改 `POINTS_PER_MIN_EARLY`。

---

## 安裝步驟（Windows）

1. 安裝 Python（3.9 或以上）。  
2. 下載本專案檔案（下面有 zip 連結），解壓縮到任意資料夾。
3. **重要：確保使用正確的 Python 環境**
   - 如果使用 conda：`conda activate py39`
   - 或直接使用：`run_terraria_timekeeper.bat`（已包含環境設定）
4. 在該資料夾開啟命令列，安裝套件：

```bash
pip install -r requirements.txt
```

4. 執行：

```bash
python terraria_timekeeper.py
```

---

## 使用方式

1. 選擇模式：
   - **玩幾小時/分鐘/秒數**：輸入小時分鐘秒數。
   - **玩到幾點（HH:MM）**：24 小時制；若時間已過，會自動算到隔天同一時刻。
2. 按 **開始**。
3. 程式會在背景監控並在剩餘 **5/3/1 分鐘** 彈出通知視窗（包含 Toast 通知與彈出視窗提醒）。
   - 5/3/1分鐘時，僅會出現該時間的彈出視窗提醒。例如:1分鐘到的時候，僅跳出1分鐘通知，不會同時出現5, 3, 1分鐘的通知。
   - 點選提醒視窗上面的ok確認按鈕，會把該提醒視窗關閉
4. 若你在時間到之前就關掉 Terraria，會依提前分鐘數加點，記錄到：
   - `rewards_log.csv`（詳細紀錄）
   - `rewards_total.json`（總點數）

> 注意：就算你開始計時時 Terraria 尚未啟動，計時依然會走；「提前」獎勵只有在 **遊戲關閉時** 且 **尚未到時間** 才會觸發。

---

## 打包成 EXE（可選）

若要做成單一 EXE 檔（方便雙擊執行），可用 [PyInstaller]:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name TerrariaTimekeeper terraria_timekeeper.py
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

---

Enjoy & 自律贏一半！🎮

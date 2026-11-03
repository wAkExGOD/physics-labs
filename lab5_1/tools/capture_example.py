"""Run the supplied executable and save real window screenshots (Windows).

No synthetic electron data are generated here. The program's original
executable is launched as a separate process; existing user windows are left
alone. Post-processing is implemented separately in ../lab5.py.
"""
from pathlib import Path
import hashlib
import json
import time
from datetime import datetime, timezone

from PIL import ImageGrab
import windows_app as win

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
win.OUT = SHOTS


def main():
    SHOTS.mkdir(exist_ok=True)
    process, main_window = win.launch()
    records = []
    try:
        controls = win.children(main_window)
        edits = sorted((c for c in controls if c["class"] == "TEdit"), key=lambda c:c["rect"][1])
        buttons = {c["text"]:c["hwnd"] for c in controls if c["class"]=="TButton"}
        page = next(c["hwnd"] for c in controls if c["class"]=="TPageControl")
        panel = next(c["hwnd"] for c in controls if c["class"]=="TPanel" and c["rect"][0]>250)
        track = next(c["hwnd"] for c in controls if c["class"]=="TTrackBar")
        menu = win.menus(win.U.GetMenu(main_window))
        scale_four = menu[1]["children"][0]["children"][3]["id"]
        win.U.SendMessageW(main_window,0x111,scale_four,0)
        cases = [("task1",v,n) for v in (40,60,120) for n in (10,1000,10000)]
        cases += [("task2",v,20000) for v in (30,37,47,61,83,120)]
        cases += [("task3",30,30000)]
        for task,voltage,count in cases:
            win.click_at(page,25,10)
            time.sleep(.06)
            win.set_text(edits[0]["hwnd"],voltage)
            win.set_text(edits[1]["hwnd"],count)
            win.U.SendMessageW(buttons["Пуск с добавлением"],0xF5,0,0)
            stem=f"{task}_{voltage}kV_{count}"
            win.capture(main_window,stem+"_window.png")
            ImageGrab.grab(window=panel).save(SHOTS/(stem+"_screen.png"))
            records.append({"task":task,"voltage_kv":voltage,"count":count,"scale":4,
                            "window":"screenshots/"+stem+"_window.png",
                            "screen":"screenshots/"+stem+"_screen.png"})
            print(stem+" saved",flush=True)

        # Compare two animation speeds at the same voltage and requested count.
        # Trackbar positions are read by ExperimentBtnClick in the original app.
        speed_results=[]
        for speed in (1,2):
            win.set_text(edits[0]["hwnd"],40)
            win.set_text(edits[1]["hwnd"],1000)
            win.U.SendMessageW(track,0x100,0x24,0)  # HOME
            win.U.SendMessageW(track,0x101,0x24,0)
            for _ in range(speed):
                win.U.SendMessageW(track,0x100,0x27,0)  # RIGHT
                win.U.SendMessageW(track,0x101,0x27,0)
            start=time.monotonic()
            win.U.SendMessageW(buttons["Пуск с добавлением"],0xF5,0,0)
            deadline=start+65
            last_log=start
            while "Стоп" in win.info(buttons["Пуск с добавлением"])["text"]:
                if time.monotonic()>deadline:
                    raise TimeoutError("Animated run did not finish")
                if time.monotonic()-last_log>10:
                    print(f"Animated speed {speed}: still running",flush=True)
                    last_log=time.monotonic()
                time.sleep(.1)
            elapsed=time.monotonic()-start
            if elapsed<1:
                raise RuntimeError("Animation speed did not take effect")
            stem=f"task1_speed{speed}_40kV_1000"
            win.capture(main_window,stem+"_window.png")
            ImageGrab.grab(window=panel).save(SHOTS/(stem+"_screen.png"))
            speed_results.append({"position":speed,"elapsed_s":elapsed,"voltage_kv":40,"count":1000,
                                  "window":"screenshots/"+stem+"_window.png"})
            print(f"Speed {speed} finished in {elapsed:.1f} s",flush=True)
        win.U.SendMessageW(track,0x100,0x24,0)
        win.U.SendMessageW(track,0x101,0x24,0)
        # Single-run statistics: 20 points with step 50 cover all 1000 releases.
        # Set the main fields as well to keep the screenshot unambiguous.
        win.set_text(edits[0]["hwnd"],40)
        win.set_text(edits[1]["hwnd"],1000)
        win.click(buttons["Одиночный пуск"])
        dialog=win.find_window(process.pid,"TListForm")
        fields=win.children(dialog)
        inputs=sorted((c for c in fields if c["class"]=="TEdit"),key=lambda c:c["rect"][1])
        for field,value in zip(inputs,(40,1000,50)):
            win.set_text(field["hwnd"],value)
        win.capture(dialog,"task1_statistics_parameters.png")
        win.click(next(c["hwnd"] for c in fields if c["class"]=="TButton" and "Принять" in c["text"]))
        prompt=win.find_window(process.pid,"#32770")
        choices=[c for c in win.children(prompt) if c["class"]=="Button"]
        yes=next((c for c in choices if "Да" in c["text"] or "Yes" in c["text"]),choices[0])
        win.click(yes["hwnd"])
        graph=win.find_window(process.pid,"TGraphForm")
        win.capture(graph,"task1_statistics_graph.png")
        win.U.PostMessageW(graph,0x10,0,0)
        time.sleep(.15)
        win.click_at(page,90,10)
        time.sleep(.15)
        win.capture(main_window,"task1_statistics_table.png")

        exe=ROOT/"app-example/difraction.exe"
        manifest={"captured_utc":datetime.now(timezone.utc).isoformat(),
                  "application":"app-example/difraction.exe",
                  "application_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
                  "runs":records,"speed_runs":speed_results,
                  "statistics":{"voltage_kv":40,"count":1000,"step":50,
                                "table":"screenshots/task1_statistics_table.png",
                                "graph":"screenshots/task1_statistics_graph.png"}}
        for path in SHOTS.glob("*.png"):
            manifest.setdefault("screenshots_sha256",{})[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        (ROOT/"results/capture_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("Capture completed. Transcribe the statistics table before processing.",flush=True)
    finally:
        process.terminate()
        process.wait(timeout=5)


if __name__=="__main__":
    main()

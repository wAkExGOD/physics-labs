"""Capture two actual animation speeds using trackbar keyboard input."""
from pathlib import Path
import hashlib
import json
import time
from PIL import ImageGrab
import windows_app as win

ROOT=Path(__file__).resolve().parents[1]
win.OUT=ROOT/"screenshots"


def main():
    process,hwnd=win.launch()
    results=[]
    try:
        controls=win.children(hwnd)
        edits=sorted((c for c in controls if c["class"]=="TEdit"),key=lambda c:c["rect"][1])
        button=next(c["hwnd"] for c in controls if c["class"]=="TButton" and c["text"]=="Пуск с добавлением")
        track=next(c["hwnd"] for c in controls if c["class"]=="TTrackBar")
        panel=next(c["hwnd"] for c in controls if c["class"]=="TPanel" and c["rect"][0]>250)
        menu=win.menus(win.U.GetMenu(hwnd))
        win.U.SendMessageW(hwnd,0x111,menu[1]["children"][0]["children"][3]["id"],0)
        for field,value in zip(edits,(40,1000)):
            win.set_text(field["hwnd"],value)
        for speed in (1,2):
            # Real trackbar key messages also update Delphi's cached Position.
            win.U.SendMessageW(track,0x100,0x24,0)  # HOME
            win.U.SendMessageW(track,0x101,0x24,0)
            for _ in range(speed):
                win.U.SendMessageW(track,0x100,0x27,0)  # RIGHT
                win.U.SendMessageW(track,0x101,0x27,0)
            actual=win.U.SendMessageW(track,0x400,0,0)  # TBM_GETPOS
            start=time.monotonic()
            win.U.SendMessageW(button,0xF5,0,0)
            print(f"Speed={speed}, actual={actual}, caption={win.info(button)['text']!r}",flush=True)
            deadline=start+65
            last=start
            while "Стоп" in win.info(button)["text"]:
                if time.monotonic()>deadline:
                    raise TimeoutError("Animated run did not finish")
                if time.monotonic()-last>10:
                    print(f"Speed {speed}: accumulating",flush=True)
                    last=time.monotonic()
                time.sleep(.1)
            elapsed=time.monotonic()-start
            if elapsed<1:
                raise RuntimeError("The animation control did not take effect")
            stem=f"task1_speed{speed}_40kV_1000"
            win.capture(hwnd,stem+"_window.png")
            ImageGrab.grab(window=panel).save(ROOT/"screenshots"/(stem+"_screen.png"))
            results.append({"position":speed,"elapsed_s":elapsed,"voltage_kv":40,"count":1000,
                            "window":"screenshots/"+stem+"_window.png"})
            print(f"Finished in {elapsed:.1f} s",flush=True)
    finally:
        process.terminate()
        process.wait(timeout=5)
    path=ROOT/"results/capture_manifest.json"
    manifest=json.loads(path.read_text(encoding="utf8"))
    manifest["speed_runs"]=results
    for path in (ROOT/"screenshots").glob("*speed*.png"):
        manifest["screenshots_sha256"][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT/"results/capture_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")


if __name__=="__main__":
    main()

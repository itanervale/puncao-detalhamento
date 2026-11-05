# -*- coding: utf-8 -*-
"""
Conferência da janela sem depender da tela: abre a janela com um projeto, passa por uma sequência de vistas e abas
do ribbon e grava cada estado em PNG pelo PrintWindow do Windows (o ImageGrab pega a tela bloqueada; o PrintWindow
desenha a própria janela). Fecha a janela no fim, sem salvar nada.

Uso:  python ferramentas/capturar_janela.py <projeto.json> [--saida PASTA]     (padrão: saidas/janela)
Requer o Pillow.
"""
import argparse
import ctypes
import os
import sys
from ctypes import wintypes

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)


class _BMI(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]


def capturar(janela, arq):
    """Grava a janela Tk (com a moldura) em PNG pelo PrintWindow (PW_RENDERFULLCONTENT)."""
    from PIL import Image
    janela.update()
    hwnd = int(janela.wm_frame(), 16)
    u32, g32 = ctypes.windll.user32, ctypes.windll.gdi32
    r = wintypes.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = u32.GetWindowDC(hwnd)
    mdc = g32.CreateCompatibleDC(hdc)
    bmp = g32.CreateCompatibleBitmap(hdc, w, h)
    g32.SelectObject(mdc, bmp)
    u32.PrintWindow(hwnd, mdc, 2)
    bmi = _BMI(ctypes.sizeof(_BMI), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    g32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    g32.DeleteObject(bmp)
    g32.DeleteDC(mdc)
    u32.ReleaseDC(hwnd, hdc)
    Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1).save(arq)
    return arq


def roteiro(app, pasta, passos):
    """Executa os passos (nome, função) com uma pausa entre eles e captura cada estado."""
    feitos = []

    def proximo(k=0):
        if k >= len(passos):
            app.modificado = False
            app.destroy()
            return
        nome, f = passos[k]
        f()
        app.update()

        def foto():
            feitos.append(capturar(app, os.path.join(pasta, f"{k + 1:02d}_{nome}.png")))
            proximo(k + 1)
        app.after(700, foto)
    app.after(1500, proximo)
    app.mainloop()
    return feitos


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    ap.add_argument("--saida", default=os.path.join(RAIZ, "saidas", "janela"))
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    from janela.app import App
    app = App(os.path.abspath(a.projeto))
    passos = [("prancha", lambda: app.ver("prancha")),
              ("planta", lambda: app.ver("planta")),
              ("corte", lambda: app.ver("corte")),
              ("conectores_ribbon", lambda: (app.rb.selecionar("Conectores"), app.ver("prancha"))),
              ("plotagem", lambda: (app.plot.set(True), app._redesenhar(), app.ver("prancha"))),
              ("tabela_ferros", lambda: (app.plot.set(False), app._redesenhar(), app.ver_tabela("ferros"))),
              ("tabela_lote", lambda: (app.rb.selecionar("Lote"), app.ver_tabela("lote"))),
              ("pilar2", lambda: (app.ir(1), app.ver("prancha")))]
    for arq in roteiro(app, a.saida, passos):
        print("gravado", arq)


if __name__ == "__main__":
    main()

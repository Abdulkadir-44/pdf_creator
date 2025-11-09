# ui/widgets/tooltip.py

import tkinter as tk

"""
Soru Otomasyon Sistemi - ToolTip Yardımcısı

Bu modül, CustomTkinter widget'ları için basit bir "hover" (üzerine gelme)
bilgi balonu (tooltip) sağlar. 

Ana Sınıf:
- ToolTip: 
  Belirli bir widget'a bağlanır ve fare üzerine geldiğinde
  metin içeren küçük bir pencere gösterir.
"""

class ToolTip:
    """
    Bir widget'ın üzerine gelindiğinde basit bir metin balonu gösterir.
    
    Metodlar:
    - __init__(self, widget, text): Tooltip'i hedeflenen widget'a bağlar.
    - show(self, event=None): Metin balonunu gösterir.
    - hide(self, event=None): Metin balonunu gizler.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 22
        y = self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#ffffe0", relief="solid", borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=4, ipady=2)

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
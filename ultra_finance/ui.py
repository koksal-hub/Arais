from __future__ import annotations

import json
import random
import threading
import tkinter as tk
from datetime import datetime, timezone
from statistics import mean
from tkinter import messagebox, ttk
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .db import Database
from .models import Decision, MarketQuote, Signal
from .risk import RiskManager


SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SHIBUSDT", "BONKUSDT", "SKYUSDT"]


class UltraFinanceApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("ULTRA Finans Ajanı v0.1 — Sanal İşlem")
        self.root.geometry("1180x720")
        self.db = Database()
        self.risk = RiskManager()
        self.quotes: dict[str, MarketQuote] = {}
        self.decisions: dict[str, Decision] = {}
        self.status = tk.StringVar(value="Hazır — gerçek emir kapalı")
        self.cash = tk.StringVar(value="-")
        self.last_signal = tk.StringVar(value="-")
        self._build()
        self._refresh_account()
        self.root.after(400, self.refresh)

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        header = ttk.Frame(self.root, padding=16)
        header.pack(fill="x")
        ttk.Label(header, text="ULTRA Finans Ajanı", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Label(header, textvariable=self.status).pack(side="right")

        cards = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        cards.pack(fill="x")
        for title, variable in (("Sanal nakit", self.cash), ("Son karar", self.last_signal)):
            box = ttk.LabelFrame(cards, text=title, padding=10)
            box.pack(side="left", fill="x", expand=True, padx=6)
            ttk.Label(box, textvariable=variable, font=("Segoe UI", 16, "bold")).pack()
        ttk.Button(cards, text="TÜM BOTLARI DURDUR", command=self._stop).pack(side="left", padx=6, ipady=12)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        market_tab = ttk.Frame(notebook, padding=10)
        agent_tab = ttk.Frame(notebook, padding=10)
        paper_tab = ttk.Frame(notebook, padding=10)
        risk_tab = ttk.Frame(notebook, padding=10)
        notebook.add(market_tab, text="Piyasalar")
        notebook.add(agent_tab, text="Ajanlar Kurulu")
        notebook.add(paper_tab, text="Sanal İşlem")
        notebook.add(risk_tab, text="Risk")

        ttk.Button(market_tab, text="Şimdi yenile", command=self.refresh).pack(anchor="w", pady=(0, 8))
        self.tree = ttk.Treeview(market_tab, columns=("symbol", "price", "change", "source"), show="headings")
        for key, title, width in (("symbol", "Sembol", 160), ("price", "Fiyat", 180), ("change", "24s %", 100), ("source", "Kaynak", 150)):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._selected)

        self.agent_text = tk.Text(agent_tab, wrap="word", font=("Consolas", 11))
        self.agent_text.pack(fill="both", expand=True)
        self.agent_text.insert("1.0", "Piyasalardan bir sembol seçin.")

        form = ttk.LabelFrame(paper_tab, text="Manuel sanal emir", padding=12)
        form.pack(fill="x")
        self.symbol_var = tk.StringVar(value="BTCUSDT")
        self.amount_var = tk.StringVar(value="100")
        ttk.Entry(form, textvariable=self.symbol_var, width=16).grid(row=0, column=0, padx=5)
        ttk.Entry(form, textvariable=self.amount_var, width=16).grid(row=0, column=1, padx=5)
        ttk.Button(form, text="Sanal AL", command=lambda: self._paper("BUY")).grid(row=0, column=2, padx=5)
        ttk.Button(form, text="Sanal SAT", command=lambda: self._paper("SELL")).grid(row=0, column=3, padx=5)
        self.positions = ttk.Treeview(paper_tab, columns=("symbol", "qty", "avg"), show="headings")
        for key, title in (("symbol", "Sembol"), ("qty", "Miktar"), ("avg", "Ortalama")):
            self.positions.heading(key, text=title)
        self.positions.pack(fill="both", expand=True, pady=10)
        self._refresh_positions()

        rules = (
            "GERÇEK EMİR: KAPALI\n\n"
            "• Kaldıraç ve vadeli işlem yasak\n"
            "• İşlem başına azami bakiye %20\n"
            "• Dokunulmaz nakit rezervi %25\n"
            "• Asgari ajan güveni %65\n"
            "• Aşırı hareketlerde işlem engeli\n"
            "• Ağ hatasında demo veri; gerçek emir yine kapalı"
        )
        ttk.Label(risk_tab, text=rules, font=("Segoe UI", 12), justify="left").pack(anchor="nw")

    def refresh(self) -> None:
        self.status.set("Piyasa verisi yenileniyor…")
        threading.Thread(target=self._load_quotes, daemon=True).start()

    def _load_quotes(self) -> None:
        quotes: list[MarketQuote] = []
        try:
            for symbol in SYMBOLS:
                url = "https://data-api.binance.vision/api/v3/ticker/24hr?" + urlencode({"symbol": symbol})
                req = Request(url, headers={"User-Agent": "UltraFinansAjani/0.1"})
                with urlopen(req, timeout=8) as response:
                    data = json.loads(response.read().decode("utf-8"))
                quotes.append(MarketQuote("Binance", symbol, float(data["lastPrice"]), float(data["priceChangePercent"]), float(data["quoteVolume"]), datetime.now(timezone.utc)))
            source = "CANLI"
        except Exception:
            source = "DEMO"
            bases = {"BTCUSDT": 65000.0, "ETHUSDT": 3400.0, "DOGEUSDT": 0.12, "SHIBUSDT": 0.000015, "BONKUSDT": 0.000022, "SKYUSDT": 0.06}
            for symbol, base in bases.items():
                move = random.uniform(-0.01, 0.01)
                quotes.append(MarketQuote("Demo", symbol, base * (1 + move), move * 100, None, datetime.now(timezone.utc)))
        self.root.after(0, lambda: self._apply_quotes(quotes, source))

    def _apply_quotes(self, quotes: list[MarketQuote], source: str) -> None:
        self.tree.delete(*self.tree.get_children())
        for quote in quotes:
            self.db.save_quote(quote)
            self.quotes[quote.symbol] = quote
            decision = self._decide(quote)
            self.decisions[quote.symbol] = decision
            self.tree.insert("", "end", iid=quote.symbol, values=(quote.symbol, self._fmt(quote.price), f"{(quote.change_24h_pct or 0):+.2f}", quote.source))
        if quotes:
            d = self.decisions[quotes[0].symbol]
            self.last_signal.set(f"{d.symbol}: {d.signal.value}")
        self.status.set(f"Hazır — {source} veri — gerçek emir kapalı")

    def _decide(self, quote: MarketQuote) -> Decision:
        prices = self.db.recent_prices(quote.symbol, 12)
        if abs(quote.change_24h_pct or 0) >= 25:
            return Decision(quote.symbol, Signal.BLOCK, 0.95, "Aşırı 24 saatlik hareket nedeniyle işlem engellendi.")
        if len(prices) < 8:
            return Decision(quote.symbol, Signal.WAIT, 0.40, "Yeterli fiyat geçmişi birikmedi.")
        short, long = mean(prices[-4:]), mean(prices[-8:])
        change = quote.change_24h_pct or 0
        if short > long and change > 1:
            return Decision(quote.symbol, Signal.BUY, 0.70, "Kısa ortalama ve 24 saatlik rejim pozitif.")
        if short < long and change < -1:
            return Decision(quote.symbol, Signal.SELL, 0.70, "Kısa ortalama ve 24 saatlik rejim negatif.")
        return Decision(quote.symbol, Signal.WAIT, 0.55, "Teknik ve rejim ajanları yeterli uzlaşma sağlayamadı.")

    def _selected(self, _event: object = None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        symbol = selected[0]
        quote, decision = self.quotes[symbol], self.decisions[symbol]
        account = self.db.account("Kripto Sanal")
        risk = self.risk.review(decision, float(account["cash_try"]))
        self.symbol_var.set(symbol)
        text = (
            f"SEMBOL: {symbol}\nFİYAT: {self._fmt(quote.price)}\n\n"
            f"KURUL KARARI: {decision.signal.value}\nGÜVEN: %{decision.confidence * 100:.0f}\n"
            f"GEREKÇE: {decision.reason}\n\n"
            f"RİSK ONAYI: {'EVET' if risk.approved else 'HAYIR'}\n"
            f"AZAMİ SANAL TUTAR: {risk.max_order_try:.2f}\n{risk.reason}"
        )
        self.agent_text.delete("1.0", "end")
        self.agent_text.insert("1.0", text)
        self.last_signal.set(f"{symbol}: {decision.signal.value}")

    def _paper(self, side: str) -> None:
        symbol = self.symbol_var.get().strip().upper()
        quote = self.quotes.get(symbol)
        if quote is None:
            messagebox.showerror("Fiyat yok", "Önce geçerli bir sembol seçin.")
            return
        try:
            amount = float(self.amount_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Hatalı tutar", "Sayısal bir tutar girin.")
            return
        decision = self.decisions.get(symbol, Decision(symbol, Signal.WAIT, 0, "Karar yok"))
        account = self.db.account("Kripto Sanal")
        risk = self.risk.review(decision, float(account["cash_try"]))
        if side == "BUY" and not risk.approved:
            messagebox.showwarning("Risk motoru reddetti", risk.reason)
            return
        if side == "BUY":
            amount = min(amount, risk.max_order_try)
            quantity = amount / quote.price
        else:
            positions = {str(p["symbol"]): p for p in self.db.positions("Kripto Sanal")}
            pos = positions.get(symbol)
            if not pos:
                messagebox.showwarning("Pozisyon yok", "Satılacak sanal pozisyon yok.")
                return
            quantity = min(float(pos["quantity"]), amount / quote.price)
        try:
            self.db.execute_paper_order("Kripto Sanal", symbol, side, quantity, quote.price, self.risk.limits.fee_rate, f"Manuel sanal işlem; kurul={decision.signal.value}")
        except (ValueError, KeyError) as exc:
            messagebox.showerror("İşlem yapılamadı", str(exc))
            return
        self._refresh_account()
        self._refresh_positions()
        messagebox.showinfo("Tamamlandı", "Yalnızca sanal işlem kaydedildi.")

    def _refresh_account(self) -> None:
        self.cash.set(f"{float(self.db.account('Kripto Sanal')['cash_try']):,.2f}")

    def _refresh_positions(self) -> None:
        self.positions.delete(*self.positions.get_children())
        for p in self.db.positions("Kripto Sanal"):
            self.positions.insert("", "end", values=(p["symbol"], f"{float(p['quantity']):.8f}", self._fmt(float(p["average_price"]))))

    def _stop(self) -> None:
        self.status.set("ACİL DURDURMA AKTİF")
        messagebox.showinfo("Acil durdurma", "Gerçek emir zaten kapalıdır; kullanıcı onayı olmadan sanal emir de açılmaz.")

    @staticmethod
    def _fmt(value: float) -> str:
        if value >= 1000:
            return f"{value:,.2f}"
        if value >= 1:
            return f"{value:.4f}"
        return f"{value:.10f}".rstrip("0")

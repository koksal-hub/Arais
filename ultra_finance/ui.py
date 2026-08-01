from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .agents import AgentCouncil
from .backtest import BacktestEngine
from .db import Database
from .market_data import BinancePublicDataClient
from .models import BacktestResult, Candle, Decision, MarketQuote, Signal, TechnicalSnapshot
from .risk import RiskManager


SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SHIBUSDT", "BONKUSDT", "SKYUSDT"]


class UltraFinanceApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("ULTRA Finans Ajanı v0.2 — Araştırma ve Sanal İşlem")
        self.root.geometry("1280x790")
        self.root.minsize(1080, 680)
        self.db = Database()
        self.market = BinancePublicDataClient()
        self.council = AgentCouncil()
        self.risk = RiskManager()
        self.backtester = BacktestEngine(self.council)
        self.quotes: dict[str, MarketQuote] = {}
        self.candles: dict[str, list[Candle]] = {}
        self.decisions: dict[str, Decision] = {}
        self.snapshots: dict[str, TechnicalSnapshot] = {}
        self.opinions: dict[str, tuple] = {}
        self._loading = False
        self.emergency_stop = False
        self.status = tk.StringVar(value="Hazır — gerçek emir kapalı")
        self.cash = tk.StringVar(value="-")
        self.equity = tk.StringVar(value="-")
        self.last_signal = tk.StringVar(value="-")
        self.selected_symbol = tk.StringVar(value="BTCUSDT")
        self.amount_var = tk.StringVar(value="100")
        self._build()
        self._refresh_account()
        self.root.after(350, self.refresh)

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        header = ttk.Frame(self.root, padding=16)
        header.pack(fill="x")
        ttk.Label(header, text="ULTRA Finans Ajanı", font=("Segoe UI", 21, "bold")).pack(side="left")
        ttk.Label(header, text="v0.2 • yalnızca araştırma ve sanal işlem", font=("Segoe UI", 10)).pack(side="left", padx=12)
        ttk.Label(header, textvariable=self.status).pack(side="right")
        cards = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        cards.pack(fill="x")
        for title, variable in (("Sanal nakit", self.cash), ("Tahmini portföy", self.equity), ("Son kurul kararı", self.last_signal)):
            box = ttk.LabelFrame(cards, text=title, padding=10)
            box.pack(side="left", fill="x", expand=True, padx=5)
            ttk.Label(box, textvariable=variable, font=("Segoe UI", 15, "bold")).pack()
        self.stop_button = ttk.Button(cards, text="ACİL DURDUR", command=self._toggle_stop)
        self.stop_button.pack(side="left", padx=6, ipady=12)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        market_tab = ttk.Frame(notebook, padding=10)
        council_tab = ttk.Frame(notebook, padding=10)
        technical_tab = ttk.Frame(notebook, padding=10)
        paper_tab = ttk.Frame(notebook, padding=10)
        backtest_tab = ttk.Frame(notebook, padding=10)
        risk_tab = ttk.Frame(notebook, padding=10)
        notebook.add(market_tab, text="Piyasalar")
        notebook.add(council_tab, text="Ajanlar Kurulu")
        notebook.add(technical_tab, text="Teknik Laboratuvar")
        notebook.add(paper_tab, text="Sanal İşlem")
        notebook.add(backtest_tab, text="Backtest")
        notebook.add(risk_tab, text="Risk ve Güvenlik")
        toolbar = ttk.Frame(market_tab)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Piyasayı yenile", command=self.refresh).pack(side="left")
        ttk.Label(toolbar, text="1 saatlik 200 mum • canlı veri yoksa deterministik demo").pack(side="left", padx=12)
        self.market_tree = ttk.Treeview(market_tab, columns=("symbol", "price", "change", "regime", "score", "decision", "source"), show="headings")
        for key, title, width in (("symbol", "Sembol", 130), ("price", "Fiyat", 160), ("change", "24s %", 85), ("regime", "Rejim", 145), ("score", "Teknik", 80), ("decision", "Karar", 90), ("source", "Kaynak", 100)):
            self.market_tree.heading(key, text=title)
            self.market_tree.column(key, width=width, anchor="center")
        self.market_tree.pack(fill="both", expand=True)
        self.market_tree.bind("<<TreeviewSelect>>", self._selected)
        self.council_text = tk.Text(council_tab, wrap="word", font=("Consolas", 11), padx=12, pady=12)
        self.council_text.pack(fill="both", expand=True)
        self.council_text.insert("1.0", "Piyasalardan bir sembol seçin.")
        self.technical_text = tk.Text(technical_tab, wrap="word", font=("Consolas", 11), padx=12, pady=12)
        self.technical_text.pack(fill="both", expand=True)
        self.technical_text.insert("1.0", "Teknik göstergeler burada gösterilecek.")
        form = ttk.LabelFrame(paper_tab, text="Manuel sanal emir", padding=12)
        form.pack(fill="x")
        ttk.Label(form, text="Sembol").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(form, textvariable=self.selected_symbol, width=16).grid(row=1, column=0, padx=5)
        ttk.Label(form, text="TL tutarı").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Entry(form, textvariable=self.amount_var, width=16).grid(row=1, column=1, padx=5)
        ttk.Button(form, text="Sanal AL", command=lambda: self._paper("BUY")).grid(row=1, column=2, padx=5)
        ttk.Button(form, text="Sanal SAT", command=lambda: self._paper("SELL")).grid(row=1, column=3, padx=5)
        ttk.Label(form, text="Gerçek borsa emri gönderilmez.").grid(row=1, column=4, padx=12)
        self.positions_tree = ttk.Treeview(paper_tab, columns=("symbol", "qty", "avg", "last", "value", "pnl"), show="headings", height=10)
        for key, title, width in (("symbol", "Sembol", 120), ("qty", "Miktar", 160), ("avg", "Ortalama", 140), ("last", "Son fiyat", 140), ("value", "Değer", 120), ("pnl", "K/Z %", 100)):
            self.positions_tree.heading(key, text=title)
            self.positions_tree.column(key, width=width, anchor="center")
        self.positions_tree.pack(fill="both", expand=True, pady=10)
        back_toolbar = ttk.Frame(backtest_tab)
        back_toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(back_toolbar, text="Seçili sembolde backtest çalıştır", command=self._run_backtest).pack(side="left")
        ttk.Label(back_toolbar, text="Sinyal kapanışta, işlem sonraki mum açılışında; komisyon ve kayma dahil.").pack(side="left", padx=12)
        self.backtest_text = tk.Text(backtest_tab, wrap="word", font=("Consolas", 11), padx=12, pady=12)
        self.backtest_text.pack(fill="both", expand=True)
        self.backtest_text.insert("1.0", "Henüz backtest çalıştırılmadı.")
        rules = (
            "GÜVENLİK ANAYASASI\n\n"
            "• Gerçek emir, para çekme, kaldıraç ve vadeli işlem kapalıdır.\n"
            "• API anahtarı istenmez; yalnızca halka açık piyasa verisi okunur.\n"
            "• İşlem başına azami sanal bakiye: %20.\n"
            "• Dokunulmaz nakit rezervi: %25.\n"
            "• Asgari kurul güveni: %65.\n"
            "• Günlük zarar limiti: %3; arka arkaya zarar limiti: 3.\n"
            "• Yüksek ATR oynaklığında Risk Gözcüsü işlemi engeller.\n"
            "• Backtest sinyali aynı mumda işleme sokmaz; sonraki açılışı kullanır.\n"
            "• İnternet yoksa demo veri açıkça işaretlenir.\n"
            "• Acil durdurma aktifken sanal emir bile açılamaz."
        )
        ttk.Label(risk_tab, text=rules, font=("Segoe UI", 12), justify="left").pack(anchor="nw")
        self._refresh_positions()

    def refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.status.set("Piyasa ve 1 saatlik mumlar yenileniyor…")
        threading.Thread(target=self._load_markets, daemon=True).start()

    def _load_markets(self) -> None:
        loaded = [self.market.load_market(symbol, interval="1h", limit=200) for symbol in SYMBOLS]
        self.root.after(0, lambda: self._apply_markets(loaded))

    def _apply_markets(self, loaded: list[tuple[MarketQuote, list[Candle], bool]]) -> None:
        self.market_tree.delete(*self.market_tree.get_children())
        live_count = 0
        for quote, candles, is_live in loaded:
            live_count += int(is_live)
            self.db.save_quote(quote)
            self.db.save_candles(candles)
            decision, snapshot, opinions = self.council.evaluate(quote.symbol, candles)
            self.db.save_decision(quote.symbol, decision.signal.value, decision.confidence, decision.reason)
            self.quotes[quote.symbol] = quote
            self.candles[quote.symbol] = candles
            self.decisions[quote.symbol] = decision
            self.snapshots[quote.symbol] = snapshot
            self.opinions[quote.symbol] = opinions
            self.market_tree.insert("", "end", iid=quote.symbol, values=(quote.symbol, self._fmt(quote.price), f"{(quote.change_24h_pct or 0):+.2f}", snapshot.regime.value, f"{snapshot.score:.0f}/100", decision.signal.value, quote.source))
        self._loading = False
        mode = "CANLI" if live_count == len(loaded) else f"KARIŞIK/DEMO ({live_count}/{len(loaded)} canlı)"
        self.status.set(f"Hazır — {mode} — gerçek emir kapalı")
        if loaded:
            symbol = self.selected_symbol.get()
            if symbol not in self.quotes:
                symbol = loaded[0][0].symbol
            self._show_symbol(symbol)
        self._refresh_account()
        self._refresh_positions()

    def _selected(self, _event: object = None) -> None:
        selected = self.market_tree.selection()
        if selected:
            self._show_symbol(selected[0])

    def _show_symbol(self, symbol: str) -> None:
        if symbol not in self.quotes:
            return
        self.selected_symbol.set(symbol)
        quote = self.quotes[symbol]
        decision = self.decisions[symbol]
        snapshot = self.snapshots[symbol]
        opinions = self.opinions[symbol]
        account = self.db.account("Kripto Sanal")
        risk = self.risk.review(decision, float(account["cash_try"]), emergency_stop=self.emergency_stop)
        lines = [f"SEMBOL: {symbol}", f"FİYAT: {self._fmt(quote.price)}  |  24s: {(quote.change_24h_pct or 0):+.2f}%", "", f"KURUL KARARI: {decision.signal.value}", f"KURUL GÜVENİ: %{decision.confidence * 100:.0f}", "", "UZMAN OYLARI"]
        for opinion in opinions:
            lines.append(f"• {opinion.agent}: {opinion.signal.value} (%{opinion.score * 100:.0f}) — {opinion.reason}")
        lines.extend(["", f"RİSK ONAYI: {'EVET' if risk.approved else 'HAYIR'}", f"AZAMİ SANAL TUTAR: {risk.max_order_try:.2f} TL", f"RİSK GEREKÇESİ: {risk.reason}", "", f"KURUL AÇIKLAMASI: {decision.reason}"])
        self.council_text.delete("1.0", "end")
        self.council_text.insert("1.0", "\n".join(lines))
        tech = [
            f"SEMBOL: {symbol}", f"REJİM: {snapshot.regime.value}", f"TEKNİK PUAN: {snapshot.score:.1f}/100", f"TEKNİK SİNYAL: {snapshot.signal.value}  |  güven %{snapshot.confidence * 100:.0f}", "",
            f"SMA20: {self._maybe(snapshot.sma_fast)}", f"SMA50: {self._maybe(snapshot.sma_slow)}", f"EMA12: {self._maybe(snapshot.ema_fast)}", f"EMA26: {self._maybe(snapshot.ema_slow)}", f"RSI14: {self._maybe(snapshot.rsi, 2)}", f"MACD: {self._maybe(snapshot.macd)}", f"MACD Sinyal: {self._maybe(snapshot.macd_signal)}", f"ATR14: {self._maybe(snapshot.atr)}", f"ATR/Fiyat: {self._pct(snapshot.atr_pct)}", f"Bollinger Üst: {self._maybe(snapshot.bollinger_upper)}", f"Bollinger Alt: {self._maybe(snapshot.bollinger_lower)}", f"Hacim Oranı: {self._maybe(snapshot.volume_ratio, 2)}", f"20 Mum Destek: {self._maybe(snapshot.support)}", f"20 Mum Direnç: {self._maybe(snapshot.resistance)}", f"Mum Formasyonları: {', '.join(snapshot.patterns) if snapshot.patterns else 'Yok'}", "", "PUAN GEREKÇELERİ"
        ]
        tech.extend(f"• {reason}" for reason in snapshot.reasons)
        self.technical_text.delete("1.0", "end")
        self.technical_text.insert("1.0", "\n".join(tech))
        self.last_signal.set(f"{symbol}: {decision.signal.value} (%{decision.confidence * 100:.0f})")

    def _paper(self, side: str) -> None:
        if self.emergency_stop:
            messagebox.showwarning("Durduruldu", "Acil durdurma aktif. Önce sistemi yeniden açın.")
            return
        symbol = self.selected_symbol.get().strip().upper()
        quote = self.quotes.get(symbol)
        if quote is None:
            messagebox.showerror("Fiyat yok", "Önce geçerli bir sembol seçin ve piyasayı yenileyin.")
            return
        try:
            amount = float(self.amount_var.get().replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hatalı tutar", "Pozitif sayısal bir TL tutarı girin.")
            return
        decision = self.decisions.get(symbol, Decision(symbol, Signal.WAIT, 0.0, "Karar yok"))
        account = self.db.account("Kripto Sanal")
        risk = self.risk.review(decision, float(account["cash_try"]), emergency_stop=self.emergency_stop)
        if side == "BUY":
            if not risk.approved:
                messagebox.showwarning("Risk motoru reddetti", risk.reason)
                return
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
            self.db.execute_paper_order("Kripto Sanal", symbol, side, quantity, quote.price, self.risk.limits.fee_rate, f"Manuel sanal işlem; kurul={decision.signal.value}; güven={decision.confidence:.2f}")
        except (ValueError, KeyError) as exc:
            messagebox.showerror("İşlem yapılamadı", str(exc))
            return
        self._refresh_account()
        self._refresh_positions()
        messagebox.showinfo("Tamamlandı", "Yalnızca sanal işlem kaydedildi.")

    def _run_backtest(self) -> None:
        symbol = self.selected_symbol.get().strip().upper()
        candles = self.candles.get(symbol)
        if not candles:
            messagebox.showwarning("Veri yok", "Önce piyasayı yenileyin ve sembol seçin.")
            return
        self.status.set(f"{symbol} backtest çalışıyor…")
        threading.Thread(target=self._backtest_worker, args=(symbol, candles.copy()), daemon=True).start()

    def _backtest_worker(self, symbol: str, candles: list[Candle]) -> None:
        try:
            result = self.backtester.run(candles)
            self.db.save_backtest(result)
            error = None
        except Exception as exc:
            result = None
            error = str(exc)
        self.root.after(0, lambda: self._show_backtest(result, error, symbol))

    def _show_backtest(self, result: BacktestResult | None, error: str | None, symbol: str) -> None:
        self.status.set("Hazır — gerçek emir kapalı")
        if error or result is None:
            messagebox.showerror("Backtest hatası", error or "Bilinmeyen hata")
            return
        pf = "-" if result.profit_factor is None else "∞" if result.profit_factor == float("inf") else f"{result.profit_factor:.2f}"
        text = (
            f"SEMBOL: {result.symbol}\nBAŞLANGIÇ: {result.starting_cash:,.2f} TL\nBİTİŞ: {result.ending_equity:,.2f} TL\n"
            f"NET GETİRİ: {result.net_return_pct:+.2f}%\nAL-TUT KARŞILAŞTIRMASI: {result.benchmark_return_pct:+.2f}%\n"
            f"MAKSİMUM DÜŞÜŞ: {result.max_drawdown_pct:.2f}%\nTAMAMLANAN İŞLEM: {result.trades}\n"
            f"KAZANAN / KAYBEDEN: {result.wins} / {result.losses}\nKAZANMA ORANI: {result.win_rate_pct:.2f}%\n"
            f"PROFIT FACTOR: {pf}\nTOPLAM KOMİSYON: {result.total_fees:.4f} TL\n\nDENETİM NOTU: {result.notes}\n\n"
            "Bu sonuç yatırım tavsiyesi veya canlı başarı garantisi değildir. 200 adet 1 saatlik mum, uzun dönem doğrulama için yetersizdir."
        )
        self.backtest_text.delete("1.0", "end")
        self.backtest_text.insert("1.0", text)
        self.last_signal.set(f"{symbol}: backtest tamamlandı")

    def _refresh_account(self) -> None:
        cash = float(self.db.account("Kripto Sanal")["cash_try"])
        position_value = 0.0
        for position in self.db.positions("Kripto Sanal"):
            symbol = str(position["symbol"])
            quote = self.quotes.get(symbol)
            position_value += float(position["quantity"]) * (quote.price if quote else float(position["average_price"]))
        self.cash.set(f"{cash:,.2f} TL")
        self.equity.set(f"{cash + position_value:,.2f} TL")

    def _refresh_positions(self) -> None:
        self.positions_tree.delete(*self.positions_tree.get_children())
        for position in self.db.positions("Kripto Sanal"):
            symbol = str(position["symbol"])
            qty = float(position["quantity"])
            avg = float(position["average_price"])
            last = self.quotes[symbol].price if symbol in self.quotes else avg
            value = qty * last
            pnl = ((last / avg) - 1.0) * 100 if avg else 0.0
            self.positions_tree.insert("", "end", values=(symbol, f"{qty:.8f}", self._fmt(avg), self._fmt(last), f"{value:,.2f}", f"{pnl:+.2f}"))

    def _toggle_stop(self) -> None:
        self.emergency_stop = not self.emergency_stop
        if self.emergency_stop:
            self.status.set("ACİL DURDURMA AKTİF")
            self.stop_button.configure(text="SİSTEMİ YENİDEN AÇ")
            messagebox.showinfo("Acil durdurma", "Sanal emirler durduruldu. Gerçek emir zaten kapalıdır.")
        else:
            self.status.set("Hazır — gerçek emir kapalı")
            self.stop_button.configure(text="ACİL DURDUR")

    @staticmethod
    def _fmt(value: float) -> str:
        if value >= 1000:
            return f"{value:,.2f}"
        if value >= 1:
            return f"{value:.4f}"
        return f"{value:.10f}".rstrip("0")

    @classmethod
    def _maybe(cls, value: float | None, digits: int | None = None) -> str:
        if value is None:
            return "-"
        if digits is not None:
            return f"{value:.{digits}f}"
        return cls._fmt(value)

    @staticmethod
    def _pct(value: float | None) -> str:
        return "-" if value is None else f"%{value * 100:.2f}"

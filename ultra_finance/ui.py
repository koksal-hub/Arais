from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .agents import MultiTimeframeCouncil
from .backtest import BacktestEngine
from .db import Database
from .market_data import BinancePublicDataClient
from .models import BacktestResult, Candle, MarketQuote, MultiTimeframeSnapshot, Signal, TechnicalSnapshot, WalkForwardResult
from .risk import RiskManager
from .strategies import BALANCED, DEFAULT_STRATEGIES, StrategyConfig
from .walkforward import WalkForwardEngine


SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SHIBUSDT", "BONKUSDT", "SKYUSDT"]
PRIMARY_INTERVAL = "1h"
CONFIRMATION_INTERVAL = "4h"


class UltraFinanceApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("ULTRA Finans Ajanı v0.3 — Çoklu Zaman ve Walk-Forward")
        self.root.geometry("1320x820")
        self.root.minsize(1120, 700)
        self.db = Database()
        self.market = BinancePublicDataClient()
        self.multi_council = MultiTimeframeCouncil(BALANCED)
        self.risk = RiskManager()
        self.walkforward = WalkForwardEngine()
        self.strategy_by_name = {strategy.name: strategy for strategy in DEFAULT_STRATEGIES}
        self.quotes: dict[str, MarketQuote] = {}
        self.candles: dict[str, dict[str, list[Candle]]] = {}
        self.mtf_snapshots: dict[str, MultiTimeframeSnapshot] = {}
        self.primary_opinions: dict[str, tuple] = {}
        self.confirmation_opinions: dict[str, tuple] = {}
        self._loading = False
        self._research_running = False
        self.emergency_stop = False
        self.status = tk.StringVar(value="Hazır — gerçek emir kapalı")
        self.cash = tk.StringVar(value="-")
        self.equity = tk.StringVar(value="-")
        self.last_signal = tk.StringVar(value="-")
        self.champion = tk.StringVar(value="Henüz belirlenmedi")
        self.selected_symbol = tk.StringVar(value="BTCUSDT")
        self.amount_var = tk.StringVar(value="100")
        self.strategy_var = tk.StringVar(value=BALANCED.name)
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
        ttk.Label(header, text="v0.3 • 1s + 4s doğrulama • sanal işlem", font=("Segoe UI", 10)).pack(side="left", padx=12)
        ttk.Label(header, textvariable=self.status).pack(side="right")

        cards = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        cards.pack(fill="x")
        for title, variable in (
            ("Sanal nakit", self.cash),
            ("Tahmini portföy", self.equity),
            ("Son kurul kararı", self.last_signal),
            ("Araştırma şampiyonu", self.champion),
        ):
            box = ttk.LabelFrame(cards, text=title, padding=10)
            box.pack(side="left", fill="x", expand=True, padx=4)
            ttk.Label(box, textvariable=variable, font=("Segoe UI", 13, "bold")).pack()
        self.stop_button = ttk.Button(cards, text="ACİL DURDUR", command=self._toggle_stop)
        self.stop_button.pack(side="left", padx=6, ipady=12)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        market_tab = ttk.Frame(notebook, padding=10)
        council_tab = ttk.Frame(notebook, padding=10)
        technical_tab = ttk.Frame(notebook, padding=10)
        paper_tab = ttk.Frame(notebook, padding=10)
        backtest_tab = ttk.Frame(notebook, padding=10)
        research_tab = ttk.Frame(notebook, padding=10)
        risk_tab = ttk.Frame(notebook, padding=10)
        notebook.add(market_tab, text="Piyasalar")
        notebook.add(council_tab, text="Ajanlar Kurulu")
        notebook.add(technical_tab, text="Çoklu Zaman Laboratuvarı")
        notebook.add(paper_tab, text="Sanal İşlem")
        notebook.add(backtest_tab, text="Backtest")
        notebook.add(research_tab, text="Strateji Laboratuvarı")
        notebook.add(risk_tab, text="Risk ve Güvenlik")

        toolbar = ttk.Frame(market_tab)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Piyasayı yenile", command=self.refresh).pack(side="left")
        ttk.Label(toolbar, text="1 saatlik karar, 4 saatlik teyit • canlı veri yoksa demo açıkça görünür").pack(side="left", padx=12)
        self.market_tree = ttk.Treeview(
            market_tab,
            columns=("symbol", "price", "change", "r1", "r4", "alignment", "decision", "source"),
            show="headings",
        )
        for key, title, width in (
            ("symbol", "Sembol", 120), ("price", "Fiyat", 150), ("change", "24s %", 80),
            ("r1", "1s Rejim", 125), ("r4", "4s Rejim", 125), ("alignment", "Uyum", 110),
            ("decision", "Karar", 90), ("source", "Kaynak", 105),
        ):
            self.market_tree.heading(key, text=title)
            self.market_tree.column(key, width=width, anchor="center")
        self.market_tree.pack(fill="both", expand=True)
        self.market_tree.bind("<<TreeviewSelect>>", self._selected)

        self.council_text = tk.Text(council_tab, wrap="word", font=("Consolas", 11), padx=12, pady=12)
        self.council_text.pack(fill="both", expand=True)
        self.council_text.insert("1.0", "Piyasalardan bir sembol seçin.")
        self.technical_text = tk.Text(technical_tab, wrap="word", font=("Consolas", 10), padx=12, pady=12)
        self.technical_text.pack(fill="both", expand=True)
        self.technical_text.insert("1.0", "1 saatlik ve 4 saatlik teknik göstergeler burada karşılaştırılacak.")

        form = ttk.LabelFrame(paper_tab, text="Manuel sanal emir", padding=12)
        form.pack(fill="x")
        ttk.Label(form, text="Sembol").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(form, textvariable=self.selected_symbol, width=16).grid(row=1, column=0, padx=5)
        ttk.Label(form, text="TL tutarı").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Entry(form, textvariable=self.amount_var, width=16).grid(row=1, column=1, padx=5)
        ttk.Button(form, text="Sanal AL", command=lambda: self._paper("BUY")).grid(row=1, column=2, padx=5)
        ttk.Button(form, text="Sanal SAT", command=lambda: self._paper("SELL")).grid(row=1, column=3, padx=5)
        ttk.Label(form, text="AL emri 1s ve 4s ortak kararı + risk onayı ister.").grid(row=1, column=4, padx=12)
        self.positions_tree = ttk.Treeview(paper_tab, columns=("symbol", "qty", "avg", "last", "value", "pnl"), show="headings", height=10)
        for key, title, width in (
            ("symbol", "Sembol", 120), ("qty", "Miktar", 160), ("avg", "Ortalama", 140),
            ("last", "Son fiyat", 140), ("value", "Değer", 120), ("pnl", "K/Z %", 100),
        ):
            self.positions_tree.heading(key, text=title)
            self.positions_tree.column(key, width=width, anchor="center")
        self.positions_tree.pack(fill="both", expand=True, pady=10)

        back_toolbar = ttk.Frame(backtest_tab)
        back_toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(back_toolbar, text="Strateji:").pack(side="left")
        ttk.Combobox(back_toolbar, textvariable=self.strategy_var, values=list(self.strategy_by_name), width=18, state="readonly").pack(side="left", padx=6)
        ttk.Button(back_toolbar, text="Seçili stratejiyi test et", command=self._run_backtest).pack(side="left")
        ttk.Label(back_toolbar, text="Komisyon + kayma dahil; emir sonraki mum açılışında.").pack(side="left", padx=12)
        self.backtest_text = tk.Text(backtest_tab, wrap="word", font=("Consolas", 11), padx=12, pady=12)
        self.backtest_text.pack(fill="both", expand=True)
        self.backtest_text.insert("1.0", "Henüz backtest çalıştırılmadı.")

        research_toolbar = ttk.Frame(research_tab)
        research_toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(research_toolbar, text="Walk-forward laboratuvarını çalıştır", command=self._run_walk_forward).pack(side="left")
        ttk.Label(research_toolbar, text="4 aday • yuvarlanan eğitim/test • şampiyon otomatik gerçek işlem yapamaz").pack(side="left", padx=12)
        self.research_text = tk.Text(research_tab, wrap="none", font=("Consolas", 10), padx=12, pady=12)
        self.research_text.pack(fill="both", expand=True)
        self.research_text.insert("1.0", "Henüz walk-forward deneyi çalıştırılmadı.")

        rules = (
            "GÜVENLİK ANAYASASI v0.3\n\n"
            "• Gerçek emir, para çekme, kaldıraç ve vadeli işlem kapalıdır.\n"
            "• API anahtarı istenmez; yalnızca halka açık piyasa verisi okunur.\n"
            "• 1 saatlik sinyal 4 saatlik rejimle çelişirse işlem BEKLE'ye çevrilir.\n"
            "• İşlem başına azami sanal bakiye: %20; nakit rezervi: %25.\n"
            "• Asgari kurul güveni: %65; günlük zarar limiti: %3.\n"
            "• Yüksek ATR oynaklığında Risk Gözcüsü işlemi engeller.\n"
            "• Backtest ve walk-forward aynı mumda sinyal + işlem yapmaz.\n"
            "• Strateji eğitim penceresinde seçilir, görülmemiş sonraki pencerede sınanır.\n"
            "• Araştırma şampiyonu, yeni canlı sanal dönem geçmeden gerçek işlem adayı değildir.\n"
            "• Acil durdurma aktifken sanal emir bile açılamaz."
        )
        ttk.Label(risk_tab, text=rules, font=("Segoe UI", 12), justify="left").pack(anchor="nw")
        self._refresh_positions()

    def refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.status.set("1s ve 4s mumlar yenileniyor…")
        threading.Thread(target=self._load_markets, daemon=True).start()

    def _load_markets(self) -> None:
        loaded: list[tuple[MarketQuote, list[Candle], list[Candle], bool]] = []
        for symbol in SYMBOLS:
            quote, primary, primary_live = self.market.load_market(symbol, interval=PRIMARY_INTERVAL, limit=240)
            _, confirmation, confirmation_live = self.market.load_market(symbol, interval=CONFIRMATION_INTERVAL, limit=180)
            loaded.append((quote, primary, confirmation, primary_live and confirmation_live))
        self.root.after(0, lambda: self._apply_markets(loaded))

    def _apply_markets(self, loaded: list[tuple[MarketQuote, list[Candle], list[Candle], bool]]) -> None:
        self.market_tree.delete(*self.market_tree.get_children())
        live_count = 0
        for quote, primary, confirmation, is_live in loaded:
            live_count += int(is_live)
            self.db.save_quote(quote)
            self.db.save_candles(primary)
            self.db.save_candles(confirmation)
            mtf, primary_opinions, confirmation_opinions = self.multi_council.evaluate(quote.symbol, primary, confirmation)
            self.db.save_decision(quote.symbol, mtf.decision.signal.value, mtf.decision.confidence, mtf.decision.reason)
            self.quotes[quote.symbol] = quote
            self.candles[quote.symbol] = {PRIMARY_INTERVAL: primary, CONFIRMATION_INTERVAL: confirmation}
            self.mtf_snapshots[quote.symbol] = mtf
            self.primary_opinions[quote.symbol] = primary_opinions
            self.confirmation_opinions[quote.symbol] = confirmation_opinions
            self.market_tree.insert("", "end", iid=quote.symbol, values=(
                quote.symbol, self._fmt(quote.price), f"{(quote.change_24h_pct or 0):+.2f}",
                mtf.primary.regime.value, mtf.confirmation.regime.value, mtf.alignment,
                mtf.decision.signal.value, quote.source,
            ))
        self._loading = False
        mode = "CANLI" if live_count == len(loaded) else f"KARIŞIK/DEMO ({live_count}/{len(loaded)} tam canlı)"
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
        mtf = self.mtf_snapshots[symbol]
        account = self.db.account("Kripto Sanal")
        risk = self.risk.review(mtf.decision, float(account["cash_try"]), emergency_stop=self.emergency_stop)
        lines = [
            f"SEMBOL: {symbol}", f"FİYAT: {self._fmt(quote.price)}  |  24s: {(quote.change_24h_pct or 0):+.2f}%", "",
            f"ÇOKLU ZAMAN KARARI: {mtf.decision.signal.value}", f"GÜVEN: %{mtf.decision.confidence * 100:.0f}",
            f"ZAMAN DİLİMİ UYUMU: {mtf.alignment}", f"GEREKÇE: {mtf.decision.reason}", "", "1 SAATLİK AJAN OYLARI",
        ]
        for opinion in self.primary_opinions[symbol]:
            lines.append(f"• {opinion.agent}: {opinion.signal.value} (%{opinion.score * 100:.0f}) — {opinion.reason}")
        lines.extend(["", "4 SAATLİK AJAN OYLARI"])
        for opinion in self.confirmation_opinions[symbol]:
            lines.append(f"• {opinion.agent}: {opinion.signal.value} (%{opinion.score * 100:.0f}) — {opinion.reason}")
        lines.extend(["", f"RİSK ONAYI: {'EVET' if risk.approved else 'HAYIR'}", f"AZAMİ SANAL TUTAR: {risk.max_order_try:.2f} TL", f"RİSK GEREKÇESİ: {risk.reason}"])
        self.council_text.delete("1.0", "end")
        self.council_text.insert("1.0", "\n".join(lines))
        technical_lines = [self._technical_block(mtf.primary), "\n" + "=" * 74 + "\n", self._technical_block(mtf.confirmation), "\n" + "=" * 74 + "\n", f"ORTAK DEĞERLENDİRME: {mtf.alignment}"]
        technical_lines.extend(f"• {reason}" for reason in mtf.reasons)
        self.technical_text.delete("1.0", "end")
        self.technical_text.insert("1.0", "\n".join(technical_lines))
        self.last_signal.set(f"{symbol}: {mtf.decision.signal.value} (%{mtf.decision.confidence * 100:.0f})")

    def _technical_block(self, snapshot: TechnicalSnapshot) -> str:
        return "\n".join([
            f"{snapshot.interval.upper()} TEKNİK RAPOR — {snapshot.strategy_name}",
            f"Rejim: {snapshot.regime.value} | Puan: {snapshot.score:.1f}/100 | Sinyal: {snapshot.signal.value}",
            f"SMA hızlı/yavaş: {self._maybe(snapshot.sma_fast)} / {self._maybe(snapshot.sma_slow)}",
            f"EMA hızlı/yavaş: {self._maybe(snapshot.ema_fast)} / {self._maybe(snapshot.ema_slow)}",
            f"RSI: {self._maybe(snapshot.rsi, 2)} | MACD: {self._maybe(snapshot.macd)} | Sinyal: {self._maybe(snapshot.macd_signal)}",
            f"ATR: {self._maybe(snapshot.atr)} | ATR/Fiyat: {self._pct(snapshot.atr_pct)}",
            f"Bollinger: {self._maybe(snapshot.bollinger_lower)} — {self._maybe(snapshot.bollinger_upper)}",
            f"Hacim oranı: {self._maybe(snapshot.volume_ratio, 2)}",
            f"Destek/Direnç: {self._maybe(snapshot.support)} / {self._maybe(snapshot.resistance)}",
            f"Mumlar: {', '.join(snapshot.patterns) if snapshot.patterns else 'Yok'}",
            "Gerekçeler:", *[f"• {reason}" for reason in snapshot.reasons],
        ])

    def _paper(self, side: str) -> None:
        if self.emergency_stop:
            messagebox.showwarning("Durduruldu", "Acil durdurma aktif. Önce sistemi yeniden açın.")
            return
        symbol = self.selected_symbol.get().strip().upper()
        quote = self.quotes.get(symbol)
        mtf = self.mtf_snapshots.get(symbol)
        if quote is None or mtf is None:
            messagebox.showerror("Fiyat yok", "Önce geçerli bir sembol seçin ve piyasayı yenileyin.")
            return
        try:
            amount = float(self.amount_var.get().replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hatalı tutar", "Pozitif sayısal bir TL tutarı girin.")
            return
        account = self.db.account("Kripto Sanal")
        risk = self.risk.review(mtf.decision, float(account["cash_try"]), emergency_stop=self.emergency_stop)
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
            self.db.execute_paper_order("Kripto Sanal", symbol, side, quantity, quote.price, self.risk.limits.fee_rate, f"Manuel sanal işlem; çoklu-zaman={mtf.decision.signal.value}; uyum={mtf.alignment}")
        except (ValueError, KeyError) as exc:
            messagebox.showerror("İşlem yapılamadı", str(exc))
            return
        self._refresh_account()
        self._refresh_positions()
        messagebox.showinfo("Tamamlandı", "Yalnızca sanal işlem kaydedildi.")

    def _run_backtest(self) -> None:
        symbol = self.selected_symbol.get().strip().upper()
        candles = self.candles.get(symbol, {}).get(PRIMARY_INTERVAL)
        if not candles:
            messagebox.showwarning("Veri yok", "Önce piyasayı yenileyin ve sembol seçin.")
            return
        strategy = self.strategy_by_name[self.strategy_var.get()]
        self.status.set(f"{symbol} / {strategy.name} backtest çalışıyor…")
        threading.Thread(target=self._backtest_worker, args=(symbol, candles.copy(), strategy), daemon=True).start()

    def _backtest_worker(self, symbol: str, candles: list[Candle], strategy: StrategyConfig) -> None:
        try:
            result = BacktestEngine(strategy).run(candles)
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
            f"SEMBOL: {result.symbol}\nSTRATEJİ: {result.strategy_name}\nBAŞLANGIÇ: {result.starting_cash:,.2f} TL\n"
            f"BİTİŞ: {result.ending_equity:,.2f} TL\nNET GETİRİ: {result.net_return_pct:+.2f}%\n"
            f"AL-TUT: {result.benchmark_return_pct:+.2f}%\nMAKSİMUM DÜŞÜŞ: {result.max_drawdown_pct:.2f}%\n"
            f"İŞLEM: {result.trades} | KAZANAN/KAYBEDEN: {result.wins}/{result.losses}\n"
            f"KAZANMA ORANI: {result.win_rate_pct:.2f}% | PROFIT FACTOR: {pf}\n"
            f"TOPLAM KOMİSYON: {result.total_fees:.4f} TL\n\nDENETİM: {result.notes}\n\n"
            "Bu tek dönem testi canlı başarı garantisi değildir; walk-forward laboratuvarıyla birlikte değerlendirilmelidir."
        )
        self.backtest_text.delete("1.0", "end")
        self.backtest_text.insert("1.0", text)
        self.last_signal.set(f"{symbol}: {result.strategy_name} testi tamamlandı")

    def _run_walk_forward(self) -> None:
        if self._research_running:
            return
        symbol = self.selected_symbol.get().strip().upper()
        candles = self.candles.get(symbol, {}).get(PRIMARY_INTERVAL)
        if not candles:
            messagebox.showwarning("Veri yok", "Önce piyasayı yenileyin ve sembol seçin.")
            return
        self._research_running = True
        self.status.set(f"{symbol} walk-forward laboratuvarı çalışıyor…")
        threading.Thread(target=self._walk_forward_worker, args=(symbol, candles.copy()), daemon=True).start()

    def _walk_forward_worker(self, symbol: str, candles: list[Candle]) -> None:
        try:
            result = self.walkforward.run(candles, train_size=120, test_size=30, step_size=30)
            self.db.save_walk_forward(result)
            error = None
        except Exception as exc:
            result = None
            error = str(exc)
        self.root.after(0, lambda: self._show_walk_forward(result, error, symbol))

    def _show_walk_forward(self, result: WalkForwardResult | None, error: str | None, symbol: str) -> None:
        self._research_running = False
        self.status.set("Hazır — gerçek emir kapalı")
        if error or result is None:
            messagebox.showerror("Walk-forward hatası", error or "Bilinmeyen hata")
            return
        self.champion.set(result.champion)
        lines = [
            f"SEMBOL: {result.symbol}", f"ARAŞTIRMA ŞAMPİYONU: {result.champion}", f"MEYDAN OKUYAN: {result.challenger or '-'}",
            f"KATMAN SAYISI: {len(result.folds)}", f"SEÇİLEN STRATEJİLERİN BİLEŞİK TEST GETİRİSİ: {result.selected_strategy_return_pct:+.2f}%",
            f"AYNI TEST PENCERELERİNDE AL-TUT: {result.selected_strategy_benchmark_pct:+.2f}%", "", "STRATEJİ LİDER TABLOSU",
            "Ad                 Kat  Ort.Get  Med.Get  Ort.DD  +Kat  İşlem  Sağlamlık", "-" * 78,
        ]
        for item in result.leaderboard:
            lines.append(f"{item.strategy_name:<18} {item.folds:>3}  {item.average_test_return_pct:>+7.2f}  {item.median_test_return_pct:>+7.2f}  {item.average_drawdown_pct:>6.2f}  {item.positive_folds:>4}  {item.total_trades:>5}  {item.robustness_score:>9.2f}")
        lines.extend(["", "YUVARLANAN KATMANLAR", "Kat  Seçilen            Eğitim Skoru  Test Get.  Al-Tut  DD  İşlem", "-" * 78])
        for fold in result.folds:
            lines.append(f"{fold.fold:>3}  {fold.selected_strategy:<18} {fold.train_score:>12.2f}  {fold.test_return_pct:>+8.2f}  {fold.test_benchmark_pct:>+6.2f}  {fold.test_drawdown_pct:>5.2f}  {fold.trades:>5}")
        lines.extend(["", f"DENETİM NOTU: {result.notes}"])
        self.research_text.delete("1.0", "end")
        self.research_text.insert("1.0", "\n".join(lines))
        self.last_signal.set(f"{symbol}: şampiyon {result.champion}")

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

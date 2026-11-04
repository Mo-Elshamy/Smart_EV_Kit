from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from config import THEME, JETSON_URL, JETSON_IP, JETSON_WEB_PORT

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineScript, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


class JetsonExplorerPage(QWidget):
    """Full-screen embedded viewer for Jetson Explorer (192.168.10.112:3000) with offline fallback."""

    def __init__(self, on_back, get_status_fn, parent=None):
        super().__init__(parent)
        self.on_back = on_back
        self.get_status_fn = get_status_fn
        self._is_active = False
        self._loaded_url = False

        self.setStyleSheet(f"background-color: {THEME['bg_dark']}; color: {THEME['text_main']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- TOP BAR (Touch Friendly for 7-inch 1080p) ---
        top_bar = QFrame()
        top_bar.setFixedHeight(90)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 14px;
                border: 2px solid #334155;
            }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 10, 15, 10)
        top_layout.setSpacing(15)

        btn_back = QPushButton("⬅ BACK TO EV DASH")
        btn_back.setFont(QFont("Segoe UI", 22, QFont.Bold))
        btn_back.setFixedSize(310, 68)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #e2e8f0;
                color: #0f172a;
                border-radius: 12px;
                border: 2px solid #94a3b8;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
        """)
        btn_back.clicked.connect(self._handle_back)
        top_layout.addWidget(btn_back)

        self.lbl_header = QLabel(f"JETSON EXPLORER  •  {JETSON_IP}:{JETSON_WEB_PORT}")
        self.lbl_header.setAlignment(Qt.AlignCenter)
        self.lbl_header.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.lbl_header.setStyleSheet("color: #f8fafc; border: none; background: transparent;")
        top_layout.addWidget(self.lbl_header, 1)

        btn_reload = QPushButton("🔄 RELOAD")
        btn_reload.setFont(QFont("Segoe UI", 22, QFont.Bold))
        btn_reload.setFixedSize(210, 68)
        btn_reload.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_cyan']};
                color: white;
                border-radius: 12px;
                border: 2px solid #0284c7;
            }}
            QPushButton:pressed {{
                background-color: #0369a1;
            }}
        """)
        btn_reload.clicked.connect(self.reload_view)
        top_layout.addWidget(btn_reload)

        layout.addWidget(top_bar)

        # --- MAIN STACK (0: Offline/Status Card, 1: Live WebEngine View) ---
        self.stack = QStackedWidget()

        # Page 0: High-contrast status / offline card
        self.status_card = QFrame()
        self.status_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 18px;
                border: 3px solid #cbd5e1;
            }
        """)
        card_layout = QVBoxLayout(self.status_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(24)
        card_layout.addStretch()

        self.lbl_card_title = QLabel("JETSON EXPLORER SYSTEM")
        self.lbl_card_title.setAlignment(Qt.AlignCenter)
        self.lbl_card_title.setFont(QFont("Segoe UI", 38, QFont.Bold))
        self.lbl_card_title.setStyleSheet("color: #0f172a; border: none;")
        card_layout.addWidget(self.lbl_card_title)

        self.lbl_card_details = QLabel("Checking connection to 192.168.10.112:3000...")
        self.lbl_card_details.setAlignment(Qt.AlignCenter)
        self.lbl_card_details.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.lbl_card_details.setStyleSheet("color: #334155; border: none;")
        self.lbl_card_details.setWordWrap(True)
        card_layout.addWidget(self.lbl_card_details)

        btn_retry = QPushButton("🔄  CONNECT / RETRY PORT 3000")
        btn_retry.setFont(QFont("Segoe UI", 26, QFont.Bold))
        btn_retry.setMinimumHeight(100)
        btn_retry.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_cyan']};
                color: white;
                border-radius: 16px;
                border: 3px solid #0284c7;
                padding: 15px 30px;
            }}
            QPushButton:pressed {{
                background-color: #0369a1;
            }}
        """)
        btn_retry.clicked.connect(self.reload_view)
        card_layout.addWidget(btn_retry)
        card_layout.addStretch()

        self.stack.addWidget(self.status_card)

        # Page 1: Embedded WebEngine View
        if HAS_WEBENGINE:
            self.webview = QWebEngineView()
            self.webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # Enable GPU hardware acceleration & WebGL
            settings = self.webview.settings()
            settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
            settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)

            # Inject Canvas roundRect polyfill at DocumentCreation
            # (Fixes Chromium <99 TypeError: ctx.roundRect is not a function which blocked 2D/3D & Leaflet)
            poly_script = QWebEngineScript()
            poly_script.setName("canvasRoundRectPolyfill")
            poly_script.setInjectionPoint(QWebEngineScript.DocumentCreation)
            poly_script.setWorldId(QWebEngineScript.MainWorld)
            poly_script.setRunsOnSubFrames(True)
            poly_script.setSourceCode("""
                (function() {
                    function polyfillRoundRect(proto) {
                        if (proto && !proto.roundRect) {
                            proto.roundRect = function(x, y, w, h, radii) {
                                if (!radii) radii = 0;
                                if (typeof radii === 'number') radii = [radii, radii, radii, radii];
                                else if (radii.length === 1) radii = [radii[0], radii[0], radii[0], radii[0]];
                                else if (radii.length === 2) radii = [radii[0], radii[1], radii[0], radii[1]];
                                else if (radii.length === 3) radii = [radii[0], radii[1], radii[2], radii[1]];
                                var tl = radii[0], tr = radii[1], br = radii[2], bl = radii[3];
                                var maxR = Math.min(Math.abs(w) / 2, Math.abs(h) / 2);
                                tl = Math.min(tl, maxR);
                                tr = Math.min(tr, maxR);
                                br = Math.min(br, maxR);
                                bl = Math.min(bl, maxR);
                                this.moveTo(x + tl, y);
                                this.arcTo(x + w, y, x + w, y + h, tr);
                                this.arcTo(x + w, y + h, x, y + h, br);
                                this.arcTo(x, y + h, x, y, bl);
                                this.arcTo(x, y, x + w, y, tl);
                                return this;
                            };
                        }
                    }
                    if (typeof CanvasRenderingContext2D !== 'undefined') polyfillRoundRect(CanvasRenderingContext2D.prototype);
                    if (typeof Path2D !== 'undefined') polyfillRoundRect(Path2D.prototype);
                })();
            """)
            self.webview.page().profile().scripts().insert(poly_script)

            self.stack.addWidget(self.webview)
        else:
            self.webview = None

        layout.addWidget(self.stack, 1)

    def open_dashboard(self):
        """Called when switching to the Jetson screen."""
        self._is_active = True
        self.refresh_status()
        status = self.get_status_fn()
        if status.get("web_online") and self.webview is not None:
            self.webview.setUrl(QUrl(JETSON_URL))
            self._loaded_url = True
            self.stack.setCurrentWidget(self.webview)
        else:
            self.stack.setCurrentWidget(self.status_card)

    def reload_view(self):
        status = self.get_status_fn()
        self.refresh_status()
        if status.get("web_online") and self.webview is not None:
            self.webview.setUrl(QUrl(JETSON_URL))
            self._loaded_url = True
            self.stack.setCurrentWidget(self.webview)
        else:
            self.stack.setCurrentWidget(self.status_card)

    def refresh_status(self):
        status = self.get_status_fn()
        host_ok = status.get("host_online", False)
        web_ok = status.get("web_online", False)
        temp_c = status.get("temp_c")
        lat_ms = status.get("latency_ms")

        temp_str = f"{temp_c:.1f}°C" if temp_c is not None else "Temp N/A"
        lat_str = f"{lat_ms:.1f} ms" if lat_ms is not None else "--"

        if web_ok:
            self.lbl_header.setText(f"🟢 JETSON EXPLORER ({JETSON_IP}:{JETSON_WEB_PORT})  •  {temp_str}  •  {lat_str}")
            if self._is_active and self.webview is not None and not self._loaded_url:
                self.webview.setUrl(QUrl(JETSON_URL))
                self._loaded_url = True
                self.stack.setCurrentWidget(self.webview)
        elif host_ok:
            self.lbl_header.setText(f"🟡 JETSON LAN ONLINE ({JETSON_IP})  •  {temp_str}  •  Ping: {lat_str}")
            self.lbl_card_title.setText("🟡 JETSON IS ONLINE — PORT 3000 NOT STARTED")
            self.lbl_card_details.setText(
                f"Jetson ({JETSON_IP}) is reachable over LAN (Latency: {lat_str}, Temp: {temp_str}),\n"
                f"but the Explorer web server on port {JETSON_WEB_PORT} is not responding yet.\n\n"
                f"Start the Explorer service on the Jetson and tap RETRY below."
            )
            self.stack.setCurrentWidget(self.status_card)
        else:
            self.lbl_header.setText(f"🔴 JETSON OFFLINE ({JETSON_IP})")
            self.lbl_card_title.setText("🔴 JETSON UNREACHABLE")
            self.lbl_card_details.setText(
                f"Cannot reach Jetson at {JETSON_IP} over Ethernet (eth0).\n"
                f"Verify that the Jetson is powered on and the LAN cable is connected."
            )
            self.stack.setCurrentWidget(self.status_card)

    def _handle_back(self):
        self._is_active = False
        self._loaded_url = False
        # Unload web page when leaving so Chromium uses 0% CPU while driving
        if self.webview is not None:
            self.webview.setUrl(QUrl("about:blank"))
        self.on_back()


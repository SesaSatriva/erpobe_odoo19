import threading

_RATE_WINDOW = 60.0
_RATE_LIMIT = 90
_RATE_LOCK = threading.Lock()
_RATE_HITS = {}
_PAGE_SIZE = 20
_CPL_TYPES = {
    "sikap": "Sikap",
    "pengetahuan": "Pengetahuan",
    "keterampilan_umum": "Keterampilan Umum",
    "keterampilan_khusus": "Keterampilan Khusus",
    "lainnya": "Lainnya",
}

import urllib.request
import json

VIETQR_BANKS_URL = "https://api.vietqr.io/v2/banks"
NAPAS_LOOKUP_URL = "https://api.vietqr.io/v2/lookup"

# Headers VietQR cần
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 ShuttleSplit/1.0",
}


def get_bank_list():
    """Fetch danh sách ngân hàng từ VietQR API"""
    try:
        req = urllib.request.Request(VIETQR_BANKS_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
            if data.get("code") == "00":
                return data.get("data", [])
    except Exception as e:
        print(f"Bank list API error: {e}")
    return _fallback_banks()


def lookup_account(bin_code: str, account_number: str):
    """Tra cứu tên chủ tài khoản qua VietQR / NAPAS"""
    try:
        payload = json.dumps({
            "bin": bin_code,
            "accountNumber": account_number
        }).encode()
        req = urllib.request.Request(
            NAPAS_LOOKUP_URL,
            data=payload,
            headers=HEADERS,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            if data.get("code") == "00" and data.get("data"):
                return {
                    "success": True,
                    "accountName": data["data"].get("accountName", ""),
                    "accountNumber": data["data"].get("accountNumber", account_number),
                }
            return {
                "success": False,
                "message": data.get("desc", "Không tìm thấy tài khoản")
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ''
        return {"success": False, "message": f"API lỗi {e.code}: {body[:100]}"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi kết nối: {str(e)}"}


def _fallback_banks():
    return [
        {"bin":"970436","code":"VCB",        "name":"Vietcombank",                  "shortName":"Vietcombank",  "logo":"https://api.vietqr.io/img/VCB.png"},
        {"bin":"970422","code":"MB",          "name":"MB Bank",                      "shortName":"MBBank",       "logo":"https://api.vietqr.io/img/MB.png"},
        {"bin":"970407","code":"TCB",         "name":"Techcombank",                  "shortName":"Techcombank",  "logo":"https://api.vietqr.io/img/TCB.png"},
        {"bin":"970432","code":"VPB",         "name":"VPBank",                       "shortName":"VPBank",       "logo":"https://api.vietqr.io/img/VPB.png"},
        {"bin":"970415","code":"VIB",         "name":"VIB",                          "shortName":"VIB",          "logo":"https://api.vietqr.io/img/VIB.png"},
        {"bin":"970418","code":"BIDV",        "name":"BIDV",                         "shortName":"BIDV",         "logo":"https://api.vietqr.io/img/BIDV.png"},
        {"bin":"422589","code":"VIETINBANK",  "name":"VietinBank",                   "shortName":"VietinBank",   "logo":"https://api.vietqr.io/img/ICB.png"},
        {"bin":"970405","code":"AGRIBANK",    "name":"Agribank",                     "shortName":"Agribank",     "logo":"https://api.vietqr.io/img/VBSP.png"},
        {"bin":"970406","code":"ACB",         "name":"ACB",                          "shortName":"ACB",          "logo":"https://api.vietqr.io/img/ACB.png"},
        {"bin":"970423","code":"TPB",         "name":"TPBank",                       "shortName":"TPBank",       "logo":"https://api.vietqr.io/img/TPB.png"},
        {"bin":"970403","code":"STB",         "name":"Sacombank",                    "shortName":"Sacombank",    "logo":"https://api.vietqr.io/img/STB.png"},
        {"bin":"970443","code":"SHB",         "name":"SHB",                          "shortName":"SHB",          "logo":"https://api.vietqr.io/img/SHB.png"},
        {"bin":"970448","code":"OCB",         "name":"OCB",                          "shortName":"OCB",          "logo":"https://api.vietqr.io/img/OCB.png"},
        {"bin":"970431","code":"EIB",         "name":"Eximbank",                     "shortName":"Eximbank",     "logo":"https://api.vietqr.io/img/EIB.png"},
        {"bin":"970416","code":"HDBANK",      "name":"HDBank",                       "shortName":"HDBank",       "logo":"https://api.vietqr.io/img/HDB.png"},
        {"bin":"970408","code":"GPB",         "name":"GPBank",                       "shortName":"GPBank",       "logo":"https://api.vietqr.io/img/GPB.png"},
        {"bin":"970419","code":"NCB",         "name":"NCB",                          "shortName":"NCB",          "logo":"https://api.vietqr.io/img/NCB.png"},
        {"bin":"970458","code":"PBVN",        "name":"Ngân hàng TNHH MTV Public VN", "shortName":"PublicBank",   "logo":""},
        {"bin":"970454","code":"VCCB",        "name":"Bản Việt (Viet Capital Bank)", "shortName":"VietCapital",  "logo":""},
        {"bin":"970452","code":"MB2",         "name":"MBBank (CN)",                  "shortName":"MBBank CN",    "logo":""},
        {"bin":"970441","code":"VRB",         "name":"VRB",                          "shortName":"VRB",          "logo":""},
        {"bin":"970462","code":"KLBVN",       "name":"KienLongBank",                 "shortName":"KienLongBank", "logo":""},
        {"bin":"970449","code":"LPB",         "name":"LPBank",                       "shortName":"LPBank",       "logo":"https://api.vietqr.io/img/LPB.png"},
        {"bin":"970472","code":"VietABank",   "name":"VietABank",                    "shortName":"VietABank",    "logo":""},
        {"bin":"970437","code":"HDBank2",     "name":"HDBank",                       "shortName":"HDBank",       "logo":""},
    ]

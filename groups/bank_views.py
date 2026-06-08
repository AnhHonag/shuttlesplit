import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from .bank_api import get_bank_list, lookup_account

_bank_cache = None

@login_required
def api_banks(request):
    global _bank_cache
    if _bank_cache is None:
        _bank_cache = get_bank_list()
    return JsonResponse({"banks": _bank_cache})


@login_required
def api_lookup_account(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST only"}, status=405)
    try:
        body = json.loads(request.body)
        bin_code = body.get("bin", "").strip()
        account = body.get("accountNumber", "").strip()
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    if not bin_code or not account:
        return JsonResponse({"success": False, "message": "Thiếu bin hoặc số tài khoản"})
    result = lookup_account(bin_code, account)
    return JsonResponse(result)

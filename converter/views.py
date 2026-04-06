import json
import base64
import io
import os

import requests
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from accounts.models import UserProfile
from .models import Conversion


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def gemini_extract(file_bytes, mime_type):
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return None, "GOOGLE_API_KEY not configured."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    b64 = base64.b64encode(file_bytes).decode('utf-8')

    prompt = """
You are an expert Data Extraction AI.

TASK:
1. Analyze the document image.
2. Infer headers if missing (Invoice, Inventory, Statement, etc.)
3. Extract tabular data accurately.
4. Standardize: convert "$1,200.00" → 1200.00, fix OCR errors.

OUTPUT (Strict JSON only):
{
    "reasoning": "Your thought process...",
    "data": [
        {"column_name": "value", ...},
        ...
    ]
}
"""
    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime_type, "data": b64}}
        ]}],
        "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
    }

    try:
        resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        result = json.loads(text)
        return result, None
    except Exception as e:
        return None, str(e)


def gemini_agent(query, df, file_bytes, mime_type):
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return "API key missing.", df

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    b64 = base64.b64encode(file_bytes).decode('utf-8')
    cols = df.columns.tolist()
    sample = df.head(5).to_csv(index=False)

    prompt = f"""
You are an Expert Multi-modal Data Agent.

USER REQUEST: "{query}"

DATAFRAME:
Columns: {cols}
Sample:
{sample}

OUTPUT (Strict JSON):
{{
    "thought": "your plan",
    "python_code": "df = ... (or null if not needed)",
    "response_text": "answer to user"
}}

PYTHON RULES:
- Must assign result back to `df`
- No markdown in python_code
"""
    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime_type, "data": b64}}
        ]}],
        "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
    }

    try:
        resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        result = json.loads(text)
        code = result.get('python_code')
        reply = result.get('response_text', 'Done.')
        if code and code != 'null':
            local_vars = {"df": df.copy(), "pd": pd}
            exec(code, {}, local_vars)
            return reply, local_vars['df']
        return reply, df
    except Exception as e:
        return f"Agent error: {e}", df


def df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
        wb = writer.book
        ws = writer.sheets['Data']
        hdr_fmt = wb.add_format({
            'bold': True, 'fg_color': '#6C5CE7', 'font_color': 'white',
            'border': 1, 'font_size': 12, 'font_name': 'Calibri'
        })
        body_fmt = wb.add_format({'border': 1, 'font_name': 'Calibri'})
        for i, col in enumerate(df.columns):
            ws.write(0, i, col, hdr_fmt)
            w = max(df[col].astype(str).map(len).max(), len(col)) + 4
            ws.set_column(i, i, w, body_fmt)
    output.seek(0)
    return output


# ─── Views ───────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    profile = get_or_create_profile(request.user)
    conversions = Conversion.objects.filter(user=request.user)[:10]
    return render(request, 'converter/dashboard.html', {
        'profile': profile,
        'conversions': conversions,
    })


@login_required
def convert(request):
    if request.method != 'POST':
        return redirect('dashboard')

    profile = get_or_create_profile(request.user)
    if not profile.can_convert:
        return JsonResponse({'error': 'Conversion limit reached. Please upgrade.'}, status=403)

    f = request.FILES.get('document')
    if not f:
        return JsonResponse({'error': 'No file uploaded.'}, status=400)

    file_bytes = f.read()
    mime_type = f.content_type
    conv = Conversion.objects.create(user=request.user, filename=f.name, status='processing')

    result, err = gemini_extract(file_bytes, mime_type)
    if err or not result:
        conv.status = 'failed'
        conv.save()
        return JsonResponse({'error': err or 'Extraction failed.'}, status=500)

    reasoning = result.get('reasoning', '')
    data = result.get('data', [])
    df = pd.DataFrame(data)

    conv.status = 'done'
    conv.rows_extracted = len(df)
    conv.reasoning = reasoning
    conv.save()

    profile.conversions_used += 1
    profile.save()

    request.session['df_json'] = df.to_json()
    request.session['reasoning'] = reasoning
    request.session['file_b64'] = base64.b64encode(file_bytes).decode()
    request.session['mime_type'] = mime_type
    request.session['chat_history'] = []

    return JsonResponse({
        'success': True,
        'reasoning': reasoning,
        'columns': df.columns.tolist(),
        'rows': df.values.tolist(),
        'total_rows': len(df),
    })


@login_required
def unlock_lifetime(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    data = json.loads(request.body)
    key = data.get('key', '')
    
    if key == 'SSAA1122':
        profile = get_or_create_profile(request.user)
        profile.is_lifetime_free = True
        profile.save()
        return JsonResponse({'success': True, 'message': 'Lifetime access unlocked!'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid security key.'}, status=400)


@login_required
def chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = json.loads(request.body)
    query = data.get('query', '')

    df_json = request.session.get('df_json')
    file_b64 = request.session.get('file_b64')
    mime_type = request.session.get('mime_type')

    if not df_json or not file_b64:
        return JsonResponse({'error': 'No active session. Please upload a document first.'}, status=400)

    df = pd.read_json(io.StringIO(df_json))
    file_bytes = base64.b64decode(file_b64)

    reply, new_df = gemini_agent(query, df, file_bytes, mime_type)
    request.session['df_json'] = new_df.to_json()

    history = request.session.get('chat_history', [])
    history.append({'role': 'user', 'content': query})
    history.append({'role': 'ai', 'content': reply})
    request.session['chat_history'] = history

    return JsonResponse({
        'reply': reply,
        'columns': new_df.columns.tolist(),
        'rows': new_df.values.tolist(),
    })


@login_required
def download_excel(request):
    df_json = request.session.get('df_json')
    if not df_json:
        return redirect('dashboard')

    df = pd.read_json(io.StringIO(df_json))
    excel_data = df_to_excel(df)

    response = HttpResponse(
        excel_data.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="dataforge_export.xlsx"'
    return response


@login_required
def workspace(request):
    df_json = request.session.get('df_json')
    reasoning = request.session.get('reasoning', '')
    chat_history = request.session.get('chat_history', [])
    profile = get_or_create_profile(request.user)

    df_data = None
    if df_json:
        df = pd.read_json(io.StringIO(df_json))
        df_data = {'columns': df.columns.tolist(), 'rows': df.values.tolist()}

    return render(request, 'converter/workspace.html', {
        'df_data': df_data,
        'reasoning': reasoning,
        'chat_history': chat_history,
        'profile': profile,
    })
